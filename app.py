from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import flash
from datetime import datetime
import pandas as pd
import sqlite3
from flask import Flask, render_template, request, session,send_file, redirect, url_for
import socket
import struct
from pymodbus.utilities import computeCRC
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from werkzeug.security import generate_password_hash
from sqlalchemy import desc
from flask import Flask, send_from_directory
from flask_migrate import Migrate
class LoginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Login')


db = SQLAlchemy()

class ModbusData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    address = db.Column(db.Integer)
    value = db.Column(db.Float)
    hex_value = db.Column(db.String(255))
    binary_value = db.Column(db.String(255))
    float_value = db.Column(db.Float)
    signed_value = db.Column(db.Float)
    is_16bit_value = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(255))  # Add a 'name' column

    def __init__(self, description, address, value, hex_value, binary_value, float_value, signed_value, is_16bit_value=False, name=None):
        self.description = description
        self.address = address
        self.value = value
        self.hex_value = hex_value
        self.binary_value = binary_value
        self.float_value = float_value
        self.signed_value = signed_value
        self.is_16bit_value = is_16bit_value
        self.name = name  # Set the 'name' when creating a ModbusData object


class ModbusData16bit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    address = db.Column(db.Integer)
    value = db.Column(db.Float)
    hex_value = db.Column(db.String(255))
    binary_value = db.Column(db.String(255))
    float_value = db.Column(db.Float)
    signed_value = db.Column(db.Float)
    name = db.Column(db.String(255))  # Add a field for the name


class User(UserMixin):
    def __init__(self, id):
        self.id = id



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'  # ชื่อฐานข้อมูล SQLite ของคุณ
db.init_app(app)
with app.app_context():
    db.create_all()
    login_manager = LoginManager()
login_manager.login_view = 'login'  # Set the login view (the route name for the login page)
login_manager.init_app(app)
app.secret_key = "your_secret_key_here"
communication_traffic = []
change_to_32bit_counter = 1  # Initialize the counter to 2
migrate = Migrate(app, db)
@login_manager.user_loader
def load_user(user_id):
    # Replace this with your actual user loading logic
    # You might want to query your database to retrieve the user by ID
    return User(user_id)

def generate_data_excel(data_list):
    df = pd.DataFrame(data_list)
    excel_filename = 'data_for_table.xlsx'
    df.to_excel(excel_filename, index=False)
    return excel_filename

def convert_to_binary_string(value, bytes_per_value):
    binary_string = bin(value)[2:]  # Convert the value to binary string excluding the '0b' prefix
    return binary_string.zfill(bytes_per_value * 8)  # Zero-fill to fit the number of bits based on bytes_per_value



@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # สร้างฟอร์ม login

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # ตรวจสอบว่าชื่อผู้ใช้และรหัสผ่านตรงกับค่าที่คุณต้องการ
        if username == 'admin' and password == 'admin':
            # สร้าง User object ขึ้นมา
            user = User(username)
            login_user(user)  # Log the user in
            return redirect(url_for('home'))  # Redirect to a protected page
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/home')
@login_required
def home():
    # This route is accessible only to authenticated users
    return render_template('home.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log the user out
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
   
    global tcp_ip, tcp_port
    return render_template('index.html', slave_id=0, function_code=0, starting_address=0, quantity=0, data_list=[],
                           is_16bit=False, communication_traffic=communication_traffic)


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

from datetime import datetime

@app.route('/search', methods=['GET'])
@login_required
def search():
    search_query = request.args.get('search_query', '')
    
    if search_query:
        try:
            search_date = datetime.strptime(search_query, '%Y-%m-%d')
            data = ModbusData.query.filter(ModbusData.date_field == search_date).all()
            save_data_to_database(data)  # บันทึกข้อมูลที่ค้นหาเข้าฐานข้อมูล
        except ValueError:
            data = ModbusData.query.filter(
                (ModbusData.description.ilike(f"%{search_query}%")) |
                (ModbusData.address.ilike(f"%{search_query}%"))
            ).all()
    else:
        data = []  # ถ้าไม่มีการค้นหาในกรณีนี้คืนรายการว่าง

    return render_template('databass.html', data=data, search_query=search_query)


@app.route('/all_data', methods=['GET'])
@login_required
def all_data():
    data = ModbusData.query.all()
    return render_template('databass.html', data=data, search_query='')



@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory('static/images', filename)





@app.route('/databass')
@login_required
def databass():
    search_query = request.args.get('search_query', '')
    show_all = request.args.get('show_all')

    data = None  # เริ่มต้นเป็น None

    show_all = request.args.get('show_all')

    if show_all == 'all':
        # Query the database for all data when 'show_all' is provided
        data = ModbusData.query.all()
    elif search_query:
        try:
            search_date = datetime.strptime(search_query, '%Y-%m-%d')
            data = ModbusData.query.filter(ModbusData.date_field == search_date).all()
        except ValueError:
            pass
    else:
        data = []  # ถ้าไม่มีการค้นหาเเล้วคืนรายการว่าง

    return render_template('databass.html', data=data, search_query=search_query)



@app.route('/index', methods=['POST'])
@login_required
def read_data():
    
    global change_to_32bit_counter  # Use the global variable

    slave_id = int(request.form['slave_id'])
    function_code = int(request.form['function_code'])
    if request.form['starting_address'] == 'custom':
        if 'custom_starting_address' in request.form:
            starting_address = int(request.form['custom_starting_address'])
        else:
            starting_address = 0  # หรือใส่ค่าเริ่มต้นที่คุณต้องการ
    else:
        starting_address = int(request.form['starting_address'])
    quantity = int(request.form['quantity'])
    tcp_ip = request.form['tcp_ip']
    tcp_port = int(request.form['tcp_port'])
    
    # Check if the data should be displayed in 16-bit format or 32-bit format
    is_16bit = request.form.get('is_16bit') == 'true'

    if is_16bit:
        bytes_per_value = 2
    else:
        bytes_per_value = 4
        if change_to_32bit_counter > 0:
            quantity *= 2
            change_to_32bit_counter -= 1

    
    
    

    # Build the request message
    request_message = bytearray(
        [slave_id, function_code, starting_address >> 8, starting_address & 0xFF, quantity >> 8, quantity & 0xFF])

    crc = computeCRC(request_message)
    request_message += crc.to_bytes(2, byteorder='big')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((tcp_ip, tcp_port))

    # Store the TX message in communication_traffic
    communication_traffic.append({'direction': 'TX', 'data': request_message.hex()})

    sock.send(request_message)

    response = sock.recv(1024)

    # Store the RX message in communication_traffic
    communication_traffic.append({'direction': 'RX', 'data': response.hex()})

    sock.close()

    data = response[3:]

    values = [int.from_bytes(data[i:i + bytes_per_value], byteorder='big', signed=False) for i in
              range(0, len(data), bytes_per_value)]
    

    if '32bit' in request.form and request.form['32bit'] == 'true':
        is_32bit = True
    else:
        is_32bit = False
    
    
    
    data_list = []
    address = starting_address
    value = 0
    
    for i, value in enumerate(values):
       
      
        
            

        
       
        
        
        address = starting_address + i * 2
               
        hex_value = hex(value)  # Convert the decimal value to HEX
        binary_value = convert_to_binary_string(value, bytes_per_value)
        float_value = struct.unpack('!f', struct.pack('!I', value))[0]
        description = f"Address {address}"
            # elster ek
        if address == 8000 or address == 8010 or address == 8020 or address == 8030 or address == 8040 or address == 8050 or address == 8060:
            description = "Time Stamp"
        if address == 8002 or address == 8012 or address == 8022 or address == 8032 or address == 8042 or address == 8052 or address == 8062:
            description = "Converted Index (VmT)"
        if address == 8004 or address == 8014 or address == 8024 or address == 8034 or address == 8044 or address == 8054 or address == 8064:
            description = "Unconverted Index (VbT)"
        if address == 8006 or address == 8016 or address == 8026 or address == 8036 or address == 8046 or address == 8056 or address == 8066:
            description = "Pressure Daily Average"
        if address == 8008 or address == 8018 or address == 8028 or address == 8038 or address == 8048 or address == 8058 or address == 8068:
            description = "Temperature Daily Average"
        if address == 7001 :
            description = "Serial No."
        if address == 7003 :
            description = "Time & Date"
        if address == 7005 :
            description = "Pressure"
        if address == 7007 :
            description = "Temperature"
        if address == 7009 :
            description = "Pressure Base"
        if address == 7011 :
            description = "Temperature base"
        if address ==  7013:
            description = " Actual Flowrate Qm"
        if address == 7015 :
            description = "Vt(Turbine index)"
        if address == 7017 :
            description = "Vm total (Actual vol cumulative)"
        if address == 7019 :
            description = "Vb total (Actual vol cumulative)"
        if address == 7021 :
            description = "AGA-8 Equation"
        if address == 7023 :
            description = "Zb"
        if address == 7025 :
            description = "Zf"
        if address == 7027 :
            description = "Pulse weight"
        if address == 7029 :
            description = "Qm max"
        if address == 7031 :
            description = "Qm min"
        if address == 7033 :
            description = "CO2"
        if address == 7035 :
            description = "N2"
        if address == 7037 :
            description = "SG"
        if address == 7039 :
            description = "LowBattery Alarm"
    
        # Actaris
        if address == 20482 :
            description = "Time Stamp"
        if address == 20498 :
            description = "Converted Index (VmT)"
        if address == 20494 :
            description = "Unconverted Index (VbT)"
        if address ==  20486:
            description = "Pressure Daily Average"
        if address ==  20484:
            description = "Temperature Daily Average"
        # config
        if address == 32 :
            description = "Specific Gravity"
        if address == 34 :
            description = "Base Pressure"
        if address == 38 :
            description = "Base Pressure. For Z Calculate"
        if address == 40 :
            description = "Base Temperature. For Z Calculate"
        if address == 42 :
            description = "Input Pulse Weight"
        if address == 44 :
            description = "Base Temperature"
        if address ==  78:
            description = " Carbon dioxide"
        if address == 82 :
            description = "Nitrogen"
        if address == 546 :
            description = "Current Time"
        if address == 756 :
            description = "Battery Alarm Warning"
        if address == 822 :
            description = "Actual Flow rate"
        if address == 824 :
            description = "Standard Flow rate"
        if address == 834 :
            description = "Current Temperature"
        if address == 836 :
            description = "Current Pressure"
        if address == 838 :
            description = "Conversion Factor"
        if address == 840 :
            description = "Act. Compressibility Factor"
        if address == 842 :
            description = "Fpv2"
        
      

        if is_16bit:
            signed_value = value - 2 ** 16 if value >= 2 ** 15 else value
            is_16bit_value = True
            float_value = value if is_16bit_value else float_value
            float_display_value = f"16-bit signed: {signed_value}, float: {float_value}"
        else:
            signed_value = value - 2 ** 32 if value >= 2 ** 31 else value
            is_16bit_value = False
            float_value = float_value if is_16bit_value else struct.unpack('!f', struct.pack('!I', value))[0]
            float_signed_value = signed_value if is_16bit_value else None  # Set signed_value to None for 32-bit
            float_display_value = float_value

        data_list.append({
            'description': description,
            'address': address,
            'value': value,
            'hex_value': hex_value,
            'binary_value': binary_value,
            'float_value': float_display_value,
            'signed_value': signed_value,
                'is_16bit': is_16bit_value,
    'float_signed_value': signed_value
            })
        value, updated_address = handle_action_configuration(i, value, address)
        # หลังจาก values = [int.from_bytes(data[i:i + bytes_per_value], byteorder='big', signed=False) for i in range(0, len(data), bytes_per_value)]
# แทนที่ด้วย:

    values = [int.from_bytes(data[i:i + bytes_per_value], byteorder='big', signed=False) for i in range(0, len(data), bytes_per_value)]

# หากต้องการแปลงเฉพาะแถวแรก สามารถทำได้เช่นนี้:


    session['tcp_ip'] = tcp_ip
    session['tcp_port'] = tcp_port
        
        
    # ตรวจสอบค่า is_16bit เพื่อเพิ่มข้อมูลลงในตาราง 16-bit
    if not is_16bit:
        # เพิ่มข้อมูลลงในตาราง 16-bit โดยเพิ่มค่าลงในตารางเดิมและเพิ่มค่าอีก 1
        data_list_16bit = []
        for data_16bit in data_list:
            address_16bit = data_16bit['address']
            value_16bit = data_16bit['value'] * 2  # เพิ่มค่าขึ้นเป็น 2 เท่าเพื่อให้เป็น 1 เท่าของข้อมูลเดิม
            data_list_16bit.append({'address': address_16bit, 'value': value_16bit})
    if 'action_actaris' in request.form: 
        
        data_list[3], data_list[7] = data_list[7], data_list[3]
        del data_list[3]
        
        data_list[4], data_list[5] = data_list[5], data_list[4]
        del data_list[3]
        data_list[5], data_list[7] = data_list[7], data_list[5]
        del data_list[4]
        data_list[4], data_list[5] = data_list[5], data_list[4]
    if 'action_configuration' in request.form:
               
      
       
        if len(data_list) >= 6:
            data_list[4], data_list[5] = data_list[5], data_list[4]
        if len(data_list) > 2:
            del data_list[2]  
        if len(data_list) >= 5:
            data_list[3], data_list[4] = data_list[4], data_list[3]
        data_list[6], data_list[22] = data_list[22], data_list[6] 
        del data_list[7] 
        data_list[7], data_list[23] = data_list[23], data_list[7] 
        
    save_data_to_database(data_list)
    

   
    data_excel_file = generate_data_excel(data_list)
    
    if 'download_data_excel' in request.form:
        return send_file(data_excel_file, as_attachment=True)


    return render_template('index.html', data_list=data_list, slave_id=slave_id, function_code=function_code,
                           starting_address=starting_address, quantity=quantity, is_16bit=is_16bit,
                           communication_traffic=communication_traffic, data=data,
                           data_excel_file=data_excel_file)

def save_data_to_database(data_list):
    try:
        for item in data_list:
            if item.get('is_16bit_value'):
                modbus_data_16bit = ModbusData16bit(
                    description=f"{item['description']} ",
                    address=item['address'],
                    value=item['value'],
                    hex_value=f"{item['value']:X}",
                    binary_value=convert_to_binary_string(item['value'], 2),
                    float_value=None,
                    signed_value=item['signed_value'],
                    is_16bit_value=True
                   
                    
                )
                db.session.add(modbus_data_16bit)
            else:
                # Here, we check if float_value is provided and not a string like '16-bit signed: 0, float: 0'
                if isinstance(item['float_value'], (float, int)):
                    float_value = item['float_value']
                else:
                    float_value = None
                
                modbus_data = ModbusData(
                    description=item['description'],
                    address=item['address'],
                    value=item['value'],
                    hex_value=item['hex_value'],
                    binary_value=item['binary_value'],
                    float_value=float_value,  # Use the corrected float_value
                    signed_value=item['signed_value'],
                    is_16bit_value=False
                )
                db.session.add(modbus_data)

        db.session.commit()
        print("Data successfully saved to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data to the database: {str(e)}")






def handle_actaris_action(i, address):
    
   
    return  address

def handle_action_configuration(i, value, address):
    

    return value, address

    # ตรวจสอบเงื่อนไขอื่น ๆ ที่คุณต้องการได้ต่อจากนี้



if __name__ == '__main__':
    app.run(debug=True)
















