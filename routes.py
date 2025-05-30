import os
from flask import Flask, flash, redirect, render_template,send_file, request, url_for, session,make_response
from app import app
from models import db, Customer, Professional, Service, Request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import time


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    admin = request.form.get('admin')

    if not username or not password or not role or (role == 'Admin' and not admin):
        flash('Please fill out all the details','danger')
        return redirect(url_for('login'))

    user = None
    session['role'] = role  

    if role == 'Customer':
        user = Customer.query.filter_by(username=username).first()
        if user :
            if user.status=="Blocked":
                flash('Your account is blocked by the admin yet.','danger')
                return redirect(url_for('blocked'))
            if  check_password_hash(user.passhash, password):
              session['customer_id'] = user.id  
              flash('Your account has been logged in successfully.','success')
              return redirect(url_for('customer_dashboard', customer_id=user.id))

        


    elif role == 'Professional':
        user = Professional.query.filter_by(username=username).first()

        if user :
            if user.status=="Blocked" and user.service.status=='Removed':
                return redirect(url_for('not_approved', professional_id=user.id))

            elif user.status=="Not Approved" or user.status=='Rejected':
                return redirect(url_for('not_approved', professional_id=user.id))

            elif user.status=="Blocked":
                return redirect(url_for('not_approved', professional_id=user.id))

            if  check_password_hash(user.passhash, password):
              session['professional_id'] = user.id  
              flash('Your account has been successfully logged in.','success')
              return redirect(url_for('professional_dashboard', professional_id=user.id))

    elif role == 'Admin' and username == 'anjali_dogra_11' and password == 'ABCDE' and admin == 'Yes':
        session['admin'] = True  
        flash('Your account has been successfully logged in.','success')
        return redirect(url_for('admin_dashboard'))

    flash('Login failed. Check your username and/or password','danger')
    return render_template('login.html')

@app.route('/not_approved/<int:professional_id>')
def not_approved(professional_id):
    professional = Professional.query.get(professional_id)
    return render_template('not_approved.html', professional=professional)


@app.route('/blocked')
def blocked():
    return render_template('blocked.html')

@app.route('/reg_professional')
def reg_professional():
    services = Service.query.all()
    return render_template('reg_professional.html',services=services)

@app.route('/reg_professional', methods=['POST'])
def reg_prof_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirmpassword = request.form.get('confirmpassword')
    name = request.form.get('name')
    experience = request.form.get('experience')
    file = request.files.get('file')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    description = request.form.get('description')
    phone_no = request.form.get('phone_no')
    service_id =  request.form.get('service')
    status = "Not Approved"

  
    service = Service.query.get(service_id)
    price = service.base_price if service else 0

    if not all([username, password, confirmpassword, phone_no,name, address, pincode, experience, file, description,service_id]):
        flash('Please fill out all the details','danger')
        return redirect(url_for('reg_professional'))

    if password != confirmpassword:
        flash('Passwords do not match','danger')
        return redirect(url_for('reg_professional'))

    professional = Professional.query.filter_by(username=username).first()
    if professional:
        flash('User already exists','danger')
        return redirect(url_for('reg_professional'))

    password_hash = generate_password_hash(password)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_professional = Professional(
            username=username,
            passhash=password_hash,
            name=name,
            experience=experience,
            address=address,
            pincode=pincode,
            description=description,
            resume_path=filename,
            service_id=service_id,
            phone_no=phone_no,
            status=status,
            price=price
            
        )

        db.session.add(new_professional)
        db.session.commit()
        return redirect(url_for('login'))

    flash('Invalid file type. Please upload a PDF or DOC/DOCX file.','danger')
    return redirect(url_for('reg_professional'))

@app.route('/reg_customer')
def reg_customer():
    return render_template('reg_customer.html')

@app.route('/reg_customer', methods=['POST'])
def reg_cust_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirmpassword = request.form.get('confirmpassword')
    name = request.form.get('name')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    phone_no = request.form.get('phone_no')
    status = 'Registered'
    if not all([username, password,phone_no, confirmpassword, name, address, pincode]):
        flash('Please fill out all the details','danger')
        return redirect(url_for('reg_customer'))

    if password != confirmpassword:
        flash('Passwords do not match','danger')
        return redirect(url_for('reg_customer'))

    customer = Customer.query.filter_by(username=username).first()
    if customer:
        flash('User already exists','danger')
        return redirect(url_for('reg_customer'))

    password_hash = generate_password_hash(password)
    new_customer = Customer(username=username,phone_no=phone_no, status=status, passhash=password_hash, name=name, address=address, pincode=pincode)
    db.session.add(new_customer)
    db.session.commit()
    return redirect(url_for('login'))


# --------------------------------------------------------------------------------------------------------------------------------------

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = Professional.query.all()
    requests = Request.query.all()
    pending_professionals = Professional.query.filter_by(status='Not Approved').all()
    return render_template('admin_dashboard.html',requests=requests,services=services,pending_professionals=pending_professionals)

@app.route('/add_service', methods=['POST'])
def add_service():
    service_name = request.form['service_name']
    base_price = request.form['base_price']
    service_description= request.form['service_description']
    time= request.form['time']
    image_url =request.form['image_url']
    status = 'Active'
    new_service = Service(service_name=service_name, status=status,base_price=base_price,service_description=service_description,image_url=image_url, time =time)
    db.session.add(new_service)
    db.session.commit()
    flash('Added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_service/<int:id>')
def delete_service(id):
    service = Service.query.get(id)
    if service:
        service.status='Removed'
        for professional in service.professionals:
            professional.status = 'Blocked' 
        db.session.commit()
        flash('Service deleted successfully', 'success')
    else:
        flash('Service not found', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_service/<int:id>', methods=['POST'])
def edit_service(id):
    service = Service.query.get(id)
    if service:
        service.service_name = request.form['service_name']
        service.base_price = request.form['base_price']
        service.time = request.form['time']
        service.service_description = request.form['service_description']
        service.image_url = request.form['image_url']
        db.session.commit()
        flash('Service updated successfully', 'success')
    else:
        flash('Service not found', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if professional:
        professional.status = "Approved"  
        db.session.commit()
        flash('Professional approved successfully!', 'success')
    else:
        flash('Professional not found!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if professional:
        professional.status = "Rejected"
        db.session.commit()
        flash('Professional rejected successfully!', 'success')
    else:
        flash('Professional not found!', 'danger')
    return redirect(url_for('admin_dashboard'))  




@app.route('/admin_search', methods=['GET'])
def admin_search():
    searchBy = request.args.get('searchBy','')
    searchText = request.args.get('searchText','')

    results = []
    service_requests = []
    
    if searchBy == 'date':
        query = Request.query.join(Customer).join(Professional)
        if searchText:
            try:
               search_date = datetime.strptime(searchText, '%Y-%m-%d').date()
               print(f"Parsed Search Date: {search_date}")
            
               query = query.filter(Request.date_of_req == search_date).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))
            except ValueError:
               flash("Invalid date format. Expected YYYY-MM-DD.",'danger')
               query = query.filter(False)
        results = query.all()


    elif searchBy == 'professional':
        query = Professional.query
        if searchText:
         query = query.filter(Professional.name.ilike(f'%{searchText}%')).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))

        professional = query.first()
        if professional:
           results = [professional]
           service_requests = Request.query.filter_by(professional_id=professional.id).all()
      
    
    elif searchBy == 'professional_rating':
        query = Professional.query.join(Request).join(Customer)
        if searchText:
            try:
               min_rating, max_rating = map(float, searchText.split('-')) 
               query = query.filter(Professional.rating >= min_rating, Professional.rating <= max_rating).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))

            except ValueError:
                query = query.filter(False)
        results = query.distinct().all()
        
    
    elif searchBy == 'customer':
        query = Customer.query
    
        if searchText:
            query = query.filter(Customer.name.ilike(f'%{searchText}%'))
        customer= query.first()
        if customer:
            results = [customer]
            service_requests = Request.query.filter_by(customer_id=customer.id).all()
    elif searchBy == 'service_status':
        query = Request.query.join(Customer).join(Professional)
        query = query.filter(Request.service_status.ilike(f'%{searchText}%')).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))
        results = query.all()

    
    elif searchBy == 'req_location':
        query = Request.query.join(Customer).join(Professional)
        query = query.filter(Customer.address.ilike(f'%{searchText}%')).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))
        results = query.all()
        
    elif searchBy == 'pincode':
        query = Request.query.join(Customer).join(Professional)
        query = query.filter(Customer.pincode.ilike(f'%{searchText}%')).filter(~(Professional.status.ilike('Blocked') & Professional.service.has(status='Removed')))
        results = query.all()

    
    return render_template('admin_search.html', service_requests=service_requests,results=results, searchBy=searchBy, searchText=searchText)





@app.route('/block_customer/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.status = "Blocked"
        db.session.commit()
        flash('Customer blocked successfully!', 'success')
    else:
        flash('Customer not found!', 'danger')
    searchBy = request.form.get('searchBy', '')
    searchText = request.form.get('searchText', '')
    print(searchBy,searchText)

    return redirect(url_for('admin_search', searchBy=searchBy, searchText=searchText))

@app.route('/unblock_customer/<int:customer_id>', methods=['POST'])
def unblock_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.status = "Registered"
        db.session.commit()
        flash('Customer unblocked successfully!', 'success')
    else:
        flash('Customer not found!', 'danger')
    searchBy = request.form.get('searchBy', '')
    searchText = request.form.get('searchText', '') 
    return redirect(url_for('admin_search', searchBy=searchBy, searchText=searchText))


@app.route('/block_professional/<int:professional_id>', methods=['POST'])
def block_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if professional:
        professional.status = "Blocked"  
        db.session.commit()
        flash('Professional blocked successfully!', 'success')
    else:
        flash('Professional not found!', 'danger')
    searchBy = request.form.get('searchBy', '')
    searchText = request.form.get('searchText', '') 
    return redirect(url_for('admin_search', searchBy=searchBy, searchText=searchText))

@app.route('/unblock_professional/<int:professional_id>', methods=['POST'])
def unblock_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if professional:
        professional.status = "Approved"  
        db.session.commit()
        flash('Professional unblocked successfully!', 'success')
    else:
        flash('Professional not found!', 'danger')
    searchBy = request.form.get('searchBy', '')
    searchText = request.form.get('searchText', '') 
    return redirect(url_for('admin_search', searchBy=searchBy, searchText=searchText))


@app.route('/admin_summary')
def admin_summary():
    return render_template('admin_summary.html',cache_buster=int(time.time()))

@app.route('/customer_ratings_chart')
def customer_ratings_chart():
    professionals = Professional.query.all()
    customers = Customer.query.all()
    requests = Request.query.all() 


    one_star = Request.query.filter_by(service_rating=1).count()
    two_star = Request.query.filter_by(service_rating=2).count()
    three_star = Request.query.filter_by( service_rating=3).count()
    four_star = Request.query.filter_by(service_rating=4).count()
    five_star = Request.query.filter_by(service_rating=5).count()

    labels = ['One star', 'Two star', 'Three star', 'Four star','Five star']
    data = [one_star, two_star, three_star, four_star,five_star]
     
    fig,ax= plt.subplots()
    ax.pie(data, labels=labels, colors=['#36A2EB', '#4BC0C0', '#9966FF', '#FF6384', '#FFCE56'], autopct='%1.1f%%')
    ax.set_title('Service Ratings')
   
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)  
    
    return send_file(img, mimetype='image/png')

@app.route('/service_status_chart_a')
def service_status_chart_a():
    requests = Request.query.all() 

    received_count = Request.query.filter_by(service_status='Requested').count()
    accepted_count = Request.query.filter_by( service_status='Accepted').count()
    closed_count = Request.query.filter_by( service_status='Closed').count()
    rejected_count = Request.query.filter_by( service_status='Rejected').count()

    
    labels = ['Requested', 'Accepted', 'Closed', 'Rejected']
    data = [received_count, accepted_count, closed_count, rejected_count]
    

    fig, ax = plt.subplots()
    ax.bar(labels, data, color=['#36A2EB', '#4BC0C0', '#9966FF', '#FF6384'])
    ax.set_ylabel('Number of Requests')
    ax.set_title('Service Requests Status')

    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig) 

    return send_file(img, mimetype='image/png')
# ---------------------------------------------------------------------------------------------------------------------------------

# Customer dashboard
@app.route('/customer_dashboard/<int:customer_id>')
def customer_dashboard(customer_id):
    services = Service.query.all()
    professionals = Professional.query.order_by(Professional.rating.desc()).all()
    
    requests = Request.query.order_by(Request.date_of_req.desc()).all()

    customer = Customer.query.get(customer_id)

    return render_template('customer_dashboard.html',requests=requests,services=services,professionals=professionals,customer=customer)


@app.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form.get('service_id')
    professional_id = request.form.get('professional_id')
    customer_id = request.form.get('customer_id')
    start_date = request.form.get('start_date')

    if not start_date:
        flash('Please fill out the start date.', 'danger')
        return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))

    try:
        start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
        current_date = datetime.today().date()
        if start_date_parsed <= current_date:
            flash('The start date must be a day after the current date.', 'danger')
            return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))

    new_request = Request(
        service_id=service_id,
        professional_id=professional_id,
        customer_id=customer_id,
        service_status="Requested",
        start_date=start_date_parsed
    )
    
    db.session.add(new_request)
    db.session.commit()

    flash('Your booking request has been submitted successfully!', 'success')
    return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))



 
@app.route('/editService/<int:req_id>', methods=['POST'])    
def editService(req_id):
    service_request = Request.query.get(req_id)
    new_start_date = request.form['start_date']
    if new_start_date:
        service_request.start_date = datetime.strptime(new_start_date, '%Y-%m-%d').date()
        db.session.commit()
        flash('Service start date updated successfully!', 'success')
    else:
        flash('Please provide a valid start date.', 'danger')
    return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))

@app.route('/edit_remarks/<int:req_id>', methods=['POST'])
def edit_remarks(req_id):
    if request.method == 'POST':
        new_remarks = request.form.get('remarks')
        service_request = Request.query.get(req_id)
        
        if service_request:
            service_request.remarks = new_remarks
            db.session.commit()
            flash("Remarks updated successfully!", "success")
        else:
            flash("Service request not found.", "danger")
    
    return redirect(url_for('customer_dashboard', customer_id=session.get('customer_id')))


@app.route('/closeService/<int:req_id>', methods=['POST'])
def closeService(req_id):
    return redirect(url_for('feedback_form', req_id=req_id))



@app.route('/feedback/<int:req_id>', methods=['GET', 'POST'])
def feedback_form(req_id):
    service_request = Request.query.get(req_id)

    



    if not service_request:
        flash("Service request not found.", "danger")
        return redirect(url_for('customer_dashboard',customer_id=session.get('customer_id')))

    if request.method == 'POST':
     
        rating = request.form.get('rating', type=float)
        remarks = request.form.get('remarks')

        if rating is None or not (1 <= rating <= 5):
            flash("Please provide a valid rating between 1 and 5.", "danger")
            return render_template('feedback_form.html', service_request=service_request)

        service_request.date_of_completion = datetime.utcnow()
        service_request.service_rating = rating
        service_request.remarks = remarks
        service_request.service_status = "Closed"

        try:
            db.session.commit()  
            
            update_professional_rating(service_request.professional_id)
            flash("Feedback submitted successfully.", "success")
            return redirect(url_for('customer_dashboard',customer_id=session.get('customer_id')))
        except Exception as e:
            db.session.rollback() 
            flash("An error occurred while submitting your feedback. Please try again.", "danger")
            return render_template('feedback_form.html', service_request=service_request)
        
        
        
       
    return render_template('feedback_form.html', service_request=service_request)

def update_professional_rating(professional_id):

    professional_requests = Request.query.filter_by(professional_id=professional_id, service_status="Closed").all()
    
    if professional_requests:
        total_rating = sum(req.service_rating for req in professional_requests if req.service_rating is not None)
        average_rating = total_rating / len(professional_requests)

      
        professional = Professional.query.get(professional_id)  
        professional.rating = average_rating
        db.session.commit() 
    else:
       
        professional = Professional.query.get(professional_id)
        professional.average_rating = None  





# Search and summary routes for Customer
@app.route('/customer_search/<int:customer_id>', methods=['GET'])
def customer_search(customer_id):
    customer = Customer.query.get(customer_id)

    
    searchBy = request.args.get('searchBy', 'service_name')
    searchText = request.args.get('searchText', '')

    professionals = db.session.query(Professional).join(Service, Professional.service_id == Service.id).filter(Professional.status == "Approved")


    if searchBy == 'location':
        professionals = professionals.filter(Professional.address.ilike(f'%{searchText}%')).order_by(Professional.rating.desc())
    elif searchBy == 'pincode':
        professionals = professionals.filter(Professional.pincode == searchText).order_by(Professional.rating.desc())
    elif searchBy == 'service_name':
        professionals = professionals.filter(Service.service_name.ilike(f'%{searchText}%')).order_by(Professional.rating.desc())

    professionals = professionals.all()

  
    return render_template('customer_search.html', professionals=professionals,customer=customer, searchBy=searchBy, searchText=searchText, customer_id=customer_id)


@app.route('/customer_summary/<int:customer_id>')
def customer_summary(customer_id):
    customer = Customer.query.get(customer_id)
    
    
    received_count = Request.query.filter_by(customer_id=customer.id, service_status='Requested').count()
    accepted_count = Request.query.filter_by(customer_id=customer.id, service_status='Accepted').count()
    closed_count = Request.query.filter_by(customer_id=customer.id, service_status='Closed').count()
    rejected_count = Request.query.filter_by(customer_id=customer.id, service_status='Rejected').count()

   
    return render_template('customer_summary.html', 
                           received_count=received_count, 
                           accepted_count=accepted_count, 
                           closed_count=closed_count, 
                           rejected_count=rejected_count,customer=customer)

@app.route('/service_status_chart/<int:customer_id>')
def service_status_chart(customer_id):
    customer = Customer.query.get(customer_id)
    
   
    received_count = Request.query.filter_by(customer_id=customer.id, service_status='Requested').count()
    accepted_count = Request.query.filter_by(customer_id=customer.id, service_status='Accepted').count()
    closed_count = Request.query.filter_by(customer_id=customer.id, service_status='Closed').count()
    rejected_count = Request.query.filter_by(customer_id=customer.id, service_status='Rejected').count()

    
    labels = ['Requested', 'Accepted', 'Closed', 'Rejected']
    data = [received_count, accepted_count, closed_count, rejected_count]

    fig, ax = plt.subplots()
    ax.bar(labels, data, color=['#36A2EB', '#4BC0C0', '#9966FF', '#FF6384'])
    ax.set_ylabel('Number of Requests')
    ax.set_title('Service Requests Status for Customer ID: {}'.format(customer_id))

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)  
    return send_file(img, mimetype='image/png')


@app.route('/customer_profile')
def customer_profile():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash('You need to log in first.','danger')
        return redirect(url_for('login'))

    customer = Customer.query.get(customer_id)
    if not customer:
        flash('Customer not found.','danger')
        return redirect(url_for('login'))

    return render_template('customer_profile.html', customer=customer)


@app.route('/edit_customer_profile', methods=['POST'])
def edit_customer_profile():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash('You need to log in first.','danger')
        return redirect(url_for('login'))

    customer = Customer.query.get(customer_id)

 
    customer.username = request.form.get('username')
    customer.email = request.form.get('email')
    customer.address = request.form.get('address')
    customer.pincode = request.form.get('pincode')
    customer.phone_no = request.form.get('phone_no')
   
    db.session.commit()
    flash('Profile updated successfully!','success')

    return redirect(url_for('customer_profile'))




# --------------------------------------------------------------------------------------------------------------------------------------
# Professional dashboard

@app.route('/professional_dashboard/<professional_id>')
def professional_dashboard(professional_id):
    
    professional = Professional.query.get(professional_id)
    
   
    services = Service.query.all()
    customers = Customer.query.all()
    requested_requests = Request.query.filter_by(professional_id=professional_id , service_status='Requested').all()
    accepted_requests = Request.query.filter_by(professional_id=professional_id , service_status='Accepted').all()
    closed_requests = Request.query.filter_by(professional_id=professional_id , service_status='Closed').all()
    
    response = make_response(render_template('professional_dashboard.html',
                                             services=services,
                                             professional=professional,
                                             customers=customers,
                                             requested_requests=requested_requests,
                                             accepted_requests=accepted_requests,
                                             closed_requests=closed_requests))

    
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


@app.route('/accept_req/<int:req_id>',methods=['POST'])
def accept_req(req_id):
    request_to_accept = Request.query.get(req_id)
    if request_to_accept:
        request_to_accept.service_status = "Accepted"
        db.session.commit()
    flash('Request Accepted successfully!','success')   
    return redirect(url_for('professional_dashboard', professional_id=session.get('professional_id')))     


@app.route('/reject_req/<int:req_id>',methods=['POST'])
def reject_req(req_id):
    request_to_reject = Request.query.get(req_id)
    if request_to_reject :
        request_to_reject.service_status = "Rejected"
        db.session.commit()
    flash('Request rejected successfully!','success')
    return redirect(url_for('professional_dashboard', professional_id=session.get('professional_id'))) 

    
# Search and summary routes for Professional



@app.route('/professional_search/<int:professional_id>', methods=['GET'])
def professional_search(professional_id):
    searchBy = request.args.get('searchBy', 'date')
    searchText = request.args.get('searchText', 'date')

    
    query = Customer.query.join(Request).filter(Request.professional_id == professional_id)

    
    
    if searchBy == 'date':
        try:
            search_date = searchText.strip()
            print(f"Search Date: {search_date}")
            query = query.filter(Request.date_of_req == search_date)
        except ValueError:
            print("Date format is incorrect. Expected YYYY-MM-DD.")
    
    elif searchBy == 'location':
        query = query.filter(Customer.address.ilike(f'%{searchText}%'))
    
    elif searchBy == 'pincode':
        query = query.filter(Customer.pincode == searchText)
    
    elif searchBy == 'name':
        query = query.filter(Customer.name.ilike(f'%{searchText}%'))

    

    customers = query.all()

  

    return render_template('professional_search.html', customers=customers, searchBy=searchBy, searchText=searchText, professional_id=professional_id)





@app.route('/professional_summary/<int:professional_id>')
def professional_summary(professional_id):
    professional = Professional.query.get(professional_id)

    return render_template('professional_summary.html',professional=professional)



@app.route('/ratings_chart/<int:professional_id>')
def ratings_chart(professional_id):
    professional = Professional.query.get(professional_id)


    one_star = Request.query.filter_by(professional_id=professional.id, service_rating=1).count()
    two_star = Request.query.filter_by(professional_id=professional.id, service_rating=2).count()
    three_star = Request.query.filter_by(professional_id=professional.id, service_rating=3).count()
    four_star = Request.query.filter_by(professional_id=professional.id, service_rating=4).count()
    five_star = Request.query.filter_by(professional_id=professional.id, service_rating=5).count()

    labels = ['one star', 'two star', 'three star', 'four star','five star']
    data = [one_star, two_star, three_star, four_star,five_star]
     
    fig,ax= plt.subplots()
    ax.pie(data, labels=labels, colors=['#36A2EB', '#4BC0C0', '#9966FF', '#FF6384', '#FFCE56'], autopct='%1.1f%%')
    ax.set_title('Service Ratings Distribution for Professional ID: {}'.format(professional_id))
   
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)  

    return send_file(img, mimetype='image/png')

@app.route('/service_status_chart_p/<int:professional_id>')  
def  service_status_chart_p(professional_id):
    professional = Professional.query.get(professional_id)


    received_count = Request.query.filter_by(professional_id=professional.id, service_status='Requested').count()
    accepted_count = Request.query.filter_by(professional_id=professional.id, service_status='Accepted').count()
    closed_count = Request.query.filter_by(professional_id=professional.id, service_status='Closed').count()
    rejected_count = Request.query.filter_by(professional_id=professional.id, service_status='Rejected').count()

    
    labels = ['Requested', 'Accepted', 'Closed', 'Rejected']
    data = [received_count, accepted_count, closed_count, rejected_count]
    

    fig, ax = plt.subplots()
    ax.bar(labels, data, color=['#36A2EB', '#4BC0C0', '#9966FF', '#FF6384'])
    ax.set_ylabel('Number of Requests')
    ax.set_title('Service Requests Status for Customer ID: {}'.format(professional_id))


    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig) 

    return send_file(img, mimetype='image/png')

@app.route('/professional_profile/<int:professional_id>')
def professional_profile(professional_id):
    professional = Professional.query.get(professional_id)
    requests = Request.query.filter_by(professional_id=professional_id, service_status='Closed').all()

    if professional:
        return render_template('professional_profile.html', requests=requests,professional=professional)
    
    flash('Professional not found!', 'danger')
    return redirect(url_for('login'))


@app.route('/edit_professional_profile/<int:professional_id>', methods=['POST'])
def edit_professional_profile(professional_id):
    professional = Professional.query.get(professional_id)
    if professional: 
        professional.username = request.form.get('username')
        professional.email = request.form.get('email')
        professional.experience = request.form.get('experience')
        professional.description = request.form.get('description')
        professional.phone_no = request.form.get('phone_no')
        professional.price = request.form.get('price')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('professional_profile', professional_id=professional_id))

    flash('Professional not found!', 'danger')
    return redirect(url_for('login'))

@app.route('/profile/<int:professional_id>')
def profile(professional_id):
  
    professional = Professional.query.get(professional_id)
    requests = Request.query.filter_by(professional_id=professional_id, service_status='Closed').all()
    if not professional:
        flash("Professional not found!", "danger")
        
    return render_template('profile.html', professional=professional,requests=requests)

# ------------------------------------------------------------------------------------------------------------------------------------
# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return render_template('login.html')

