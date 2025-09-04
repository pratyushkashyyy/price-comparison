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


class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobQueueManager:
    def __init__(self, max_concurrent_jobs=1):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_queue = queue.Queue()
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
    
    def add_job(self, job_id, product_url):
        """Add a job to the queue"""
        with self.job_lock:
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
            self.job_queue.put((job_id, product_url))
            print(f"Job {job_id} added to queue. Queue size: {self.job_queue.qsize()}")
    
    def _worker_loop(self):
        """Main worker loop that processes jobs from the queue"""
        while self.is_running:
            try:
                # Wait for a job with timeout to allow checking is_running
                job_id, product_url = self.job_queue.get(timeout=1)
                
                # Check if we can start this job (respect max concurrent limit)
                if len(self.running_jobs) >= self.max_concurrent_jobs:
                    # Put job back in queue and wait
                    self.job_queue.put((job_id, product_url))
                    sleep(1)
                    continue
                
                # Start processing the job
                self._process_job(job_id, product_url)
                
            except queue.Empty:
                # No jobs in queue, continue loop
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
        db = SessionLocal()
        try:
            # Update job status to processing
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                return
            
            job.status = JobStatus.PROCESSING.value
            db.commit()
            
            print(f"Processing job {job_id}...")
            
            # Process the product
            result, page_id = product_details_api(product_url)
            
            # Update job with result
            job.status = JobStatus.COMPLETED.value
            job.result = result
            job.page_id = page_id
            job.completed_at = datetime.now(pytz.timezone('Asia/Kolkata'))
            db.commit()
            
            print(f"Job {job_id} completed successfully")
            
        except Exception as e:
            # Update job with error
            if job:
                job.status = JobStatus.FAILED.value
                job.error = str(e)
                job.completed_at = datetime.now(pytz.timezone('Asia/Kolkata'))
                db.commit()
            print(f"Job {job_id} failed: {e}")
        finally:
            db.close()
            # Remove from running jobs
            with self.job_lock:
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
    
    def get_queue_status(self):
        """Get current queue status"""
        with self.job_lock:
            return {
                "queue_size": self.job_queue.qsize(),
                "running_jobs": len(self.running_jobs),
                "max_concurrent": self.max_concurrent_jobs,
                "running_job_ids": list(self.running_jobs.keys())
            }


# Initialize the job queue manager
job_queue_manager = JobQueueManager(max_concurrent_jobs=1)




@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def product_details_api(product_url):
        pageId = get_shortcode(product_url)
        print("Page ID: ", pageId)
        try:
            print(f"Checking readiness for product {pageId}")
            percentage = ready_check(pageId)
            if percentage == 'No product detail steps found':
                percentage = 100
            else:
                while percentage < 90:
                    print(f"Waiting for product to load... {percentage}%")
                    percentage = ready_check(pageId)
                    sleep(1)
        except Exception as e:
                return {'error': f'Failed to check readiness attempts: {str(e)}'}
        if pageId:
            product_details = get_details_product(pageId)
            try:
                short_code = pageId
                db = SessionLocal()
                try:
                    indian_tz = pytz.timezone('Asia/Kolkata')
                    timestamp = datetime.now(indian_tz)
                    
                    # Check if product exists and update it
                    existing_product = db.query(Product).filter(Product.productUrl == product_url).first()
                    if existing_product:
                        # Update existing product
                        existing_product.shortCode = short_code
                        existing_product.timestamp = timestamp
                        db.commit()
                        print(f"Product updated: ID={existing_product.id}, Code={short_code}")
                    else:
                        # Create new product if it doesn't exist
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
    use_job = request.args.get("job", "false").lower() == "true"
    
    if not productUrl:
        return jsonify({"error": "Missing required parameter 'productUrl'"}), 400
    
    db = SessionLocal()
    try:
        indian_tz = pytz.timezone('Asia/Kolkata')
        one_day_ago = datetime.now(indian_tz) - timedelta(days=1)
        existing_product = db.query(Product).filter(
            Product.productUrl == productUrl, 
            Product.timestamp >= one_day_ago
        ).first()
        
        if existing_product:
            print("Product already exists in database (within 1 day)")
            pageId = existing_product.shortCode
            result = get_details_product(pageId)
            if isinstance(result, str):
                try:
                    result = clean_unicode_text(json.loads(result))
                except json.JSONDecodeError:
                    pass
            
            if updater == "true":
                return jsonify({"pageid": pageId}), 200
            return jsonify(result), 200
        
        # If using job system, create job and add to queue
        if use_job:
            job_id = str(uuid.uuid4())
            job = Job(
                job_id=job_id,
                product_url=productUrl,
                status=JobStatus.PENDING.value
            )
            db.add(job)
            db.commit()
            
            # Add job to queue for processing
            job_queue_manager.add_job(job_id, productUrl)
            
            return jsonify({
                "job_id": job_id,
                "status": "pending",
                "message": "Job created successfully. Use /status/{job_id} to check progress.",
                "queue_position": job_queue_manager.get_queue_status()["queue_size"]
            }), 202
        
        # Fallback to synchronous processing
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
            
            # Add queue information for pending/queued jobs
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
        # Note: This is a simple implementation. In production, you might want to 
        # mark jobs as cancelled in the database instead of just clearing the queue
        with job_queue_manager.job_lock:
            # Clear the queue
            while not job_queue_manager.job_queue.empty():
                try:
                    job_queue_manager.job_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Update all pending/queued jobs in database to cancelled
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

@app.route("/<path:url>", methods=["GET"]) 
def root(url):
    if not url:
        return jsonify({"error": "Missing required parameter 'url'"}), 400
    result = product_details_api(url)
    if isinstance(result, str):
        try:
            result = clean_unicode_text(json.loads(result))
        except json.JSONDecodeError:
            pass
    return jsonify(result), 200

if __name__ == "__main__":
    # Initialize database tables
    from model import init_db
    init_db()
    
    # Start the job queue manager
    job_queue_manager.start()
    
    try:
        app.run(host="0.0.0.0", port=9999, debug=True)
    finally:
        # Stop the job queue manager when the app shuts down
        job_queue_manager.stop()
