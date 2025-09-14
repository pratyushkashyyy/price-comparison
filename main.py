import requests, json
from details_product import get_details_product, clean_unicode_text
from checkforready import ready_check
from time import sleep
from flask import Flask, jsonify, render_template, request
from model import SessionLocal, Product, Job
from datetime import datetime, timedelta
import pytz
from fetch_shortcode import get_shortcode
import threading
import uuid
import queue
from enum import Enum

app = Flask(__name__)

def send_completion_webhook(page_id, product_url):
    """Send webhook notification when a job is completed"""
    webhook_url = "https://appdeals.in/webhook/flash-data"
    payload = {
        "pageId": page_id,
        "productUrl": product_url
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Webhook sent successfully for pageId: {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send webhook for pageId {page_id}: {e}")
        return False

class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobQueueManager:
    def __init__(self, max_concurrent_jobs=1, max_queue_size=100):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_queue_size = max_queue_size
        self.job_queue = queue.Queue(maxsize=max_queue_size)
        self.running_jobs = {}
        self.job_lock = threading.Lock()
        self.worker_thread = None
        self.is_running = False
        
    def start(self):
        """Start the job queue worker thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("Job queue manager started")
    
    def stop(self):
        """Stop the job queue worker thread"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        print("Job queue manager stopped")
    
    def check_duplicate_job(self, product_url):
        """Check if there's already a pending or queued job for the same product URL"""
        db = SessionLocal()
        try:
            existing_job = db.query(Job).filter(
                Job.product_url == product_url,
                Job.status.in_([JobStatus.PENDING.value, JobStatus.QUEUED.value, JobStatus.PROCESSING.value])
            ).first()
            return existing_job
        finally:
            db.close()
    
    def add_job_simple(self, job_id, product_url):
        """Add a job to the queue without deduplication check (for internal use)"""
        with self.job_lock:
            # Check if queue is full
            if self.job_queue.qsize() >= self.max_queue_size:
                print(f"❌ Queue is full (max size: {self.max_queue_size}). Cannot add job {job_id}")
                return {
                    "success": False,
                    "queue_full": True,
                    "message": f"Queue is full (max size: {self.max_queue_size})"
                }
            
            # Update job status to queued
            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = JobStatus.QUEUED.value
                    db.commit()
            finally:
                db.close()
            
            # Add to queue
            try:
                self.job_queue.put_nowait((job_id, product_url))
                print(f"Job {job_id} added to queue. Queue size: {self.job_queue.qsize()}")
                return {
                    "success": True,
                    "queue_position": self.job_queue.qsize(),
                    "message": "Job added to queue successfully"
                }
            except queue.Full:
                print(f"❌ Queue is full. Cannot add job {job_id}")
                return {
                    "success": False,
                    "queue_full": True,
                    "message": "Queue is full"
                }
    
    def add_job(self, job_id, product_url):
        """Add a job to the queue with deduplication"""
        with self.job_lock:
            # Check for duplicate jobs first
            existing_job = self.check_duplicate_job(product_url)
            if existing_job:
                print(f"🔄 Duplicate job detected for URL: {product_url}")
                print(f"   Existing job ID: {existing_job.job_id}, Status: {existing_job.status}")
                return {
                    "success": False,
                    "duplicate": True,
                    "existing_job_id": existing_job.job_id,
                    "existing_status": existing_job.status,
                    "message": "A job for this URL is already pending, queued, or processing"
                }
            
            # Use the simple add method
            return self.add_job_simple(job_id, product_url)
    
    def _worker_loop(self):
        """Main worker loop that processes jobs from the queue"""
        while self.is_running:
            try:
                job_id, product_url = self.job_queue.get(timeout=1)
                
                if len(self.running_jobs) >= self.max_concurrent_jobs:
                    self.job_queue.put((job_id, product_url))
                    sleep(1)
                    continue
                
                self._process_job(job_id, product_url)
                
                # Wait for the job to complete before processing the next one
                if job_id in self.running_jobs:
                    self.running_jobs[job_id].join()
                    print(f"⏳ Job {job_id} completed. Waiting 30 seconds before processing next job...")
                    sleep(30)  # Wait 30 seconds after each job completes
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker loop: {e}")
                sleep(1)
    
    def _process_job(self, job_id, product_url):
        """Process a single job"""
        with self.job_lock:
            self.running_jobs[job_id] = threading.Thread(
                target=self._execute_job, 
                args=(job_id, product_url),
                daemon=True
            )
            self.running_jobs[job_id].start()
    
    def _execute_job(self, job_id, product_url):
        """Execute the actual job processing"""
        print(f"🚀 Starting job execution for {job_id} with URL: {product_url}")
        start_time = datetime.now()
        
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                print(f"❌ Job {job_id} not found in database")
                return
            
            indian_tz = pytz.timezone('Asia/Kolkata')
            one_day_ago = datetime.now(indian_tz) - timedelta(days=1)
            existing_product = db.query(Product).filter(
                Product.productUrl == product_url, 
                Product.timestamp >= one_day_ago
            ).first()
            
            if existing_product:
                print(f"📋 Product already exists in database (within 1 day) - Page ID: {existing_product.shortCode}")
                result = get_details_product(existing_product.shortCode)
                page_id = existing_product.shortCode
                
                job.status = JobStatus.COMPLETED.value
                job.result = result
                job.page_id = page_id
                job.completed_at = datetime.now(pytz.timezone('Asia/Kolkata'))
                db.commit()
                
                # Send webhook notification
                send_completion_webhook(page_id, product_url)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"✅ Job {job_id} completed successfully using existing product in {duration:.2f} seconds")
                print(f"📊 Result type: {type(result)}, Page ID: {page_id}")
                return
            
            job.status = JobStatus.PROCESSING.value
            db.commit()
            print(f"📝 Job {job_id} status updated to PROCESSING")
            
            print(f"🔄 Calling product_details_api for {product_url}")
            result, page_id = product_details_api(product_url)
            
            job.status = JobStatus.COMPLETED.value
            job.result = result
            job.page_id = page_id
            job.completed_at = datetime.now(pytz.timezone('Asia/Kolkata'))
            db.commit()
            
            # Send webhook notification
            send_completion_webhook(page_id, product_url)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ Job {job_id} completed successfully in {duration:.2f} seconds")
            print(f"📊 Result type: {type(result)}, Page ID: {page_id}")
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            if job:
                job.status = JobStatus.FAILED.value
                job.error = str(e)
                job.completed_at = datetime.now(pytz.timezone('Asia/Kolkata'))
                db.commit()
            print(f"❌ Job {job_id} failed after {duration:.2f} seconds: {e}")
            import traceback
            print(f"🔍 Full error traceback:\n{traceback.format_exc()}")
        finally:
            db.close()
            with self.job_lock:
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
                    print(f"🧹 Job {job_id} removed from running jobs")
    
    def get_queue_status(self):
        """Get current queue status"""
        with self.job_lock:
            return {
                "queue_size": self.job_queue.qsize(),
                "max_queue_size": self.max_queue_size,
                "running_jobs": len(self.running_jobs),
                "max_concurrent": self.max_concurrent_jobs,
                "running_job_ids": list(self.running_jobs.keys()),
                "queue_utilization": f"{(self.job_queue.qsize() / self.max_queue_size) * 100:.1f}%"
            }

job_queue_manager = JobQueueManager(max_concurrent_jobs=1, max_queue_size=100)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def product_details_api(product_url):
        print(f"🔗 Starting product_details_api for URL: {product_url}")
        start_time = datetime.now()
        
        print(f"📱 Calling get_shortcode for: {product_url}")
        shortcode_start = datetime.now()
        pageId = get_shortcode(product_url)
        shortcode_duration = (datetime.now() - shortcode_start).total_seconds()
        print(f"📱 get_shortcode completed in {shortcode_duration:.2f} seconds")
        print(f"📱 Page ID: {pageId}")
        
        try:
            print(f"🔍 Checking readiness for product {pageId}")
            readiness_start = datetime.now()
            percentage = ready_check(pageId)
            readiness_duration = (datetime.now() - readiness_start).total_seconds()
            print(f"🔍 Initial readiness check completed in {readiness_duration:.2f} seconds: {percentage}%")
            
            if percentage == 'No product detail steps found':
                percentage = 100
                print(f"🔍 No product detail steps found, setting percentage to 100%")
            else:
                wait_count = 0
                while percentage < 90:
                    wait_count += 1
                    print(f"⏳ Waiting for product to load... {percentage}% (attempt {wait_count})")
                    readiness_start = datetime.now()
                    percentage = ready_check(pageId)
                    readiness_duration = (datetime.now() - readiness_start).total_seconds()
                    print(f"⏳ Readiness check {wait_count} completed in {readiness_duration:.2f} seconds: {percentage}%")
                    sleep(1)
                    
                    if wait_count > 60:
                        print(f"⏰ Timeout reached after {wait_count} attempts, proceeding with current percentage: {percentage}%")
                        break
        except Exception as e:
                print(f"❌ Error during readiness check: {e}")
                return {'error': f'Failed to check readiness attempts: {str(e)}'}
        if pageId:
            print(f"📊 Processing product with pageId: {pageId}")
            product_details = get_details_product(pageId)
            try:
                short_code = pageId
                db = SessionLocal()
                try:
                    indian_tz = pytz.timezone('Asia/Kolkata')
                    timestamp = datetime.now(indian_tz)
                    
                    existing_product = db.query(Product).filter(Product.productUrl == product_url).first()
                    if existing_product:
                        existing_product.shortCode = short_code
                        existing_product.timestamp = timestamp
                        db.commit()
                        print(f"Product updated: ID={existing_product.id}, Code={short_code}")
                    else:
                        product = Product(
                            productUrl=product_url,
                            shortCode=short_code,
                            timestamp=timestamp
                        )
                        db.add(product)
                        db.commit()
                        db.refresh(product)
                        print(f"New product stored in database: ID={product.id}, Code={short_code}")
                except Exception as e:
                    db.rollback()
                    print(f"❌ Database storage failed: {e}")
                finally:
                    db.close()       
            except Exception as e:
                    print(f"❌ Database operation failed: {e}")
            return product_details, pageId
        else:
            print(f"❌ No pageId extracted from URL: {product_url}")
            return {'error': f'Could not extract pageId from URL. The URL might not be a valid product URL or Flash.co could not process it.'}, None

@app.route("/view", methods=["GET"]) 
def view():
    product_url = request.args.get("url")
    if not product_url:
        return jsonify({"error": "Missing required parameter 'url'"}), 400
    return render_template("response.html", url=product_url)

@app.route("/api", methods=["GET"]) 
def api():
    productUrl = request.args.get("url")
    updater = request.args.get("updater")
    use_job = request.args.get("job", "true").lower() == "true"
    
    if not productUrl:
        return jsonify({"error": "Missing required parameter 'url'"}), 400
    
    db = SessionLocal()
    try:      
        if use_job:
            # Check if product already exists within the last day
            indian_tz = pytz.timezone('Asia/Kolkata')
            one_day_ago = datetime.now(indian_tz) - timedelta(days=1)
            existing_product = db.query(Product).filter(
                Product.productUrl == productUrl, 
                Product.timestamp >= one_day_ago
            ).first()
            
            if existing_product:
                print(f"Product already exists in database (within 1 day) - Page ID: {existing_product.shortCode}")
                result = get_details_product(existing_product.shortCode)
                if updater == "true":
                    return jsonify({"pageid": existing_product.shortCode}), 200
                if use_job == "true":
                    return jsonify({"pageid": existing_product.shortCode}), 200
                return jsonify(result), 200
            
            # Check for duplicate jobs before creating a new one
            existing_job = job_queue_manager.check_duplicate_job(productUrl)
            if existing_job:
                return jsonify({
                    "job_id": existing_job.job_id,
                    "status": existing_job.status,
                    "message": "A job for this URL is already pending, queued, or processing",
                    "duplicate": True,
                    "queue_position": job_queue_manager.get_queue_status()["queue_size"]
                }), 409  # Conflict status code
            
            # Product doesn't exist, create a new job
            job_id = str(uuid.uuid4())
            job = Job(
                job_id=job_id,
                product_url=productUrl,
                status=JobStatus.PENDING.value
            )
            db.add(job)
            db.commit()
            
            # Add job to queue (no need for deduplication check here since we already checked)
            add_result = job_queue_manager.add_job_simple(job_id, productUrl)
            
            if add_result["success"]:
                return jsonify({
                    "job_id": job_id,
                    "status": "pending",
                    "message": "Job created successfully. Use /status/{job_id} to check progress.",
                    "queue_position": add_result["queue_position"]
                }), 202
            else:
                return jsonify({
                    "error": add_result["message"],
                    "queue_status": job_queue_manager.get_queue_status()
                }), 503  # Service unavailable
        else:
            # Synchronous processing (for backward compatibility)
            result, pageId = product_details_api(productUrl)
            if isinstance(result, str):
                try:
                    result = clean_unicode_text(json.loads(result))
                except json.JSONDecodeError:
                    pass
            
            if updater == "true":
                return jsonify({"pageid": pageId}), 200
            return jsonify(result), 200
        
    finally:
        db.close()

@app.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get the status of a job"""
    try:
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                return jsonify({"error": "Job not found"}), 404
            
            response_data = {
                "job_id": job.job_id,
                "status": job.status,
                "product_url": job.product_url,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            
            if job.status in [JobStatus.PENDING.value, JobStatus.QUEUED.value]:
                queue_status = job_queue_manager.get_queue_status()
                response_data["queue_info"] = {
                    "queue_position": queue_status["queue_size"],
                    "running_jobs": queue_status["running_jobs"],
                    "max_concurrent": queue_status["max_concurrent"]
                }
            
            if job.status == JobStatus.COMPLETED.value:
                response_data["result"] = job.result
                response_data["page_id"] = job.page_id
            elif job.status == JobStatus.FAILED.value:
                response_data["error"] = job.error
            
            return jsonify(response_data), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch job status: {str(e)}"}), 500

@app.route("/jobs", methods=["GET"])
def get_jobs():
    """Get all jobs with optional status filter"""
    try:
        db = SessionLocal()
        try:
            status_filter = request.args.get("status")
            query = db.query(Job)
            
            if status_filter:
                query = query.filter(Job.status == status_filter)
            
            jobs = query.order_by(Job.created_at.desc()).limit(50).all()
            
            job_list = []
            for job in jobs:
                job_data = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "product_url": job.product_url,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                if job.status == "completed":
                    job_data["page_id"] = job.page_id
                elif job.status == "failed":
                    job_data["error"] = job.error
                
                job_list.append(job_data)
            
            return jsonify({"jobs": job_list}), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch jobs: {str(e)}"}), 500

@app.route("/products", methods=["GET"])
def get_products():
    try:
        db = SessionLocal()
        try:
            products = db.query(Product).all()
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'productUrl': product.productUrl,
                    'shortCode': product.shortCode,
                    'timestamp': product.timestamp.isoformat()
                })
            return jsonify({'products': product_list}), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products: {str(e)}'}), 500

@app.route("/products/<short_code>", methods=["GET"])
def get_product_by_code(short_code):
    try:
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.shortCode == short_code).first()
            if product:
                return jsonify({
                    'id': product.id,
                    'productUrl': product.productUrl,
                    'shortCode': product.shortCode,
                    'timestamp': product.timestamp.isoformat()
                }), 200
            else:
                return jsonify({'error': 'Product not found'}), 404
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch product: {str(e)}'}), 500

@app.route("/queue/status", methods=["GET"])
def get_queue_status():
    """Get current queue status and statistics"""
    try:
        queue_status = job_queue_manager.get_queue_status()
        return jsonify(queue_status), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch queue status: {str(e)}"}), 500

@app.route("/queue/clear", methods=["POST"])
def clear_queue():
    """Clear all pending jobs from the queue"""
    try:
        with job_queue_manager.job_lock:
            while not job_queue_manager.job_queue.empty():
                try:
                    job_queue_manager.job_queue.get_nowait()
                except queue.Empty:
                    break
            
            db = SessionLocal()
            try:
                db.query(Job).filter(
                    Job.status.in_([JobStatus.PENDING.value, JobStatus.QUEUED.value])
                ).update({"status": "cancelled"})
                db.commit()
            finally:
                db.close()
        
        return jsonify({"message": "Queue cleared successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to clear queue: {str(e)}"}), 500

@app.route("/queue/pause", methods=["POST"])
def pause_queue():
    """Pause the job queue (jobs will remain in queue but won't be processed)"""
    try:
        job_queue_manager.is_running = False
        return jsonify({"message": "Queue paused successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to pause queue: {str(e)}"}), 500

@app.route("/queue/resume", methods=["POST"])
def resume_queue():
    """Resume the job queue"""
    try:
        job_queue_manager.start()
        return jsonify({"message": "Queue resumed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to resume queue: {str(e)}"}), 500

@app.route("/job/start", methods=["POST"])
def start_job():
    """Start a job and check if product exists first"""
    try:
        data = request.get_json()
        if not data or 'product_url' not in data:
            return jsonify({"error": "Missing required parameter 'product_url'"}), 400
        
        product_url = data['product_url']
        
        db = SessionLocal()
        try:
            # Check if product already exists within the last day
            indian_tz = pytz.timezone('Asia/Kolkata')
            one_day_ago = datetime.now(indian_tz) - timedelta(days=1)
            existing_product = db.query(Product).filter(
                Product.productUrl == product_url, 
                Product.timestamp >= one_day_ago
            ).first()
            
            if existing_product:
                print(f"Product already exists in database (within 1 day) - Page ID: {existing_product.shortCode}")
                return jsonify({
                    "exists": True,
                    "page_id": existing_product.shortCode,
                    "message": "Product already exists in database"
                }), 200
            
            # Check for duplicate jobs before creating a new one
            existing_job = job_queue_manager.check_duplicate_job(product_url)
            if existing_job:
                return jsonify({
                    "exists": False,
                    "job_id": existing_job.job_id,
                    "status": existing_job.status,
                    "message": "A job for this URL is already pending, queued, or processing",
                    "duplicate": True,
                    "queue_position": job_queue_manager.get_queue_status()["queue_size"]
                }), 409
            
            # Product doesn't exist, create a new job
            job_id = str(uuid.uuid4())
            job = Job(
                job_id=job_id,
                product_url=product_url,
                status=JobStatus.PENDING.value
            )
            db.add(job)
            db.commit()
            
            # Add job to queue for processing (no deduplication check needed)
            add_result = job_queue_manager.add_job_simple(job_id, product_url)
            
            if add_result["success"]:
                return jsonify({
                    "exists": False,
                    "job_id": job_id,
                    "status": "pending",
                    "message": "Product not found. Job created and queued for processing.",
                    "queue_position": add_result["queue_position"]
                }), 202
            else:
                return jsonify({
                    "exists": False,
                    "error": add_result["message"],
                    "queue_status": job_queue_manager.get_queue_status()
                }), 503  # Service unavailable
            
        finally:
            db.close()
    except Exception as e:
        return jsonify({"error": f"Failed to start job: {str(e)}"}), 500

# @app.route("/<path:url>", methods=["GET"]) 
# def root(url):
#     if not url:
#         return jsonify({"error": "Missing required parameter 'url'"}), 400
#     result, pageId = product_details_api(url)
#     if isinstance(result, str):
#         try:
#             result = clean_unicode_text(json.loads(result))
#         except json.JSONDecodeError:
#             pass
#     return jsonify(result), 200

if __name__ == "__main__":
    import sys
    from model import init_db
    init_db()
    
    # Check if URL is provided as command line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Processing single URL: {url}")
        
        # Process the URL directly
        result, page_id = product_details_api(url)
        if isinstance(result, str):
            try:
                result = clean_unicode_text(json.loads(result))
            except json.JSONDecodeError:
                pass
        
        # Send webhook notification for direct execution
        if page_id:
            print(f"📤 Sending webhook notification for pageId: {page_id}")
            webhook_success = send_completion_webhook(page_id, url)
            if webhook_success:
                print(f"✅ Webhook sent successfully")
            else:
                print(f"❌ Webhook failed to send")
        
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Page ID: {page_id}")
    else:
        job_queue_manager.start()
        
        try:
            app.run(host="0.0.0.0", port=9999, debug=True)
        finally:
            job_queue_manager.stop()
