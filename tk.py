import tkinter as tk
from tkinter import ttk
import socket
from pymodbus.utilities import computeCRC
from tkinter import messagebox
# Create a Tkinter application window
app = tk.Tk()
app.title("Modbus Data")
username_entry = None
password_entry = None
# Function to check login credentials
def check_login():
    # For simplicity, let's use hardcoded credentials
    username = "admin"
    password = "admin"

    global username_entry, password_entry

    entered_username = username_entry.get()
    entered_password = password_entry.get()

    if entered_username == username and entered_password == password:
        login_window.destroy()  # Close the login window
        app.deiconify()  # Show the main application window
    else:
        messagebox.showerror("Login Error", "Invalid username or password")

# Function to open the login window
def open_login_window():
    app.withdraw()  # Hide the main application window

    global login_window, username_entry, password_entry
    login_window = tk.Toplevel(app)
    login_window.title("Login")

    # Create labels and entry fields for login
    tk.Label(login_window, text="Username").grid(row=0, column=0, padx=10, pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(login_window, text="Password").grid(row=1, column=0, padx=10, pady=5)
    password_entry = tk.Entry(login_window, show="*")  # Show * for password
    password_entry.grid(row=1, column=1, padx=10, pady=5)

    # Create a button to submit login credentials
    login_button = ttk.Button(login_window, text="Login", command=check_login)
    login_button.grid(row=2, column=0, columnspan=2, pady=10)
# Function to toggle between data types
open_login_window()
app.withdraw()



def toggle_data_type():
    current_data_type = data_type_var.get()
    if current_data_type == "32-bit":
        data_type_var.set("16-bit")
    elif current_data_type == "16-bit":
        data_type_var.set("None")
    elif current_data_type == "None":
        data_type_var.set("32-bit")

# Create Tkinter variables to store user input
slave_id_var = tk.StringVar()
function_code_var = tk.StringVar()
starting_address_var = tk.StringVar()
quantity_var = tk.StringVar()
tcp_ip_var = tk.StringVar()
tcp_port_var = tk.StringVar()
data_type_var = tk.StringVar()
data_type_var.set("32-bit")  # Default data type

# Create a frame to group radio buttons
data_type_frame = ttk.LabelFrame(app, text="Data Type", padding=(10, 5))
data_type_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Function to toggle between data types
def toggle_data_type():
    pass  # Implement your toggle_data_type function here

bit16_button = ttk.Radiobutton(data_type_frame, text="16-bit", variable=data_type_var, value="16-bit", command=toggle_data_type)
bit16_button.grid(row=0, column=0)

bit32_button = ttk.Radiobutton(data_type_frame, text="32-bit", variable=data_type_var, value="32-bit", command=toggle_data_type)
bit32_button.grid(row=0, column=1)

none_button = ttk.Radiobutton(data_type_frame, text="None", variable=data_type_var, value="None", command=toggle_data_type)
none_button.grid(row=0, column=2)

# Create a frame for user input and Modbus Connection Status
input_frame = ttk.LabelFrame(app, text="User Input and Modbus Connection Status", padding=(10, 5))
input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Create labels and entry fields for user input inside the input_frame
tk.Label(input_frame, text="Slave ID").grid(row=0, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=slave_id_var).grid(row=0, column=1, padx=10, pady=5)

tk.Label(input_frame, text="Function Code").grid(row=1, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=function_code_var).grid(row=1, column=1, padx=10, pady=5)

tk.Label(input_frame, text="Starting Address").grid(row=2, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=starting_address_var).grid(row=2, column=1, padx=10, pady=5)

tk.Label(input_frame, text="Quantity").grid(row=3, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=quantity_var).grid(row=3, column=1, padx=10, pady=5)

tk.Label(input_frame, text="TCP IP Address").grid(row=4, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=tcp_ip_var).grid(row=4, column=1, padx=10, pady=5)

tk.Label(input_frame, text="TCP Port").grid(row=5, column=0, padx=10, pady=5)
tk.Entry(input_frame, textvariable=tcp_port_var).grid(row=5, column=1, padx=10, pady=5)

# Create a Label for Modbus Connection Status inside the input_frame
connection_status_var = tk.StringVar()
connection_status_var.set("Modbus Connection: Not Connected")
connection_status_label = tk.Label(input_frame, textvariable=connection_status_var, font=("Helvetica", 12))
connection_status_label.grid(row=6, columnspan=2, padx=10, pady=10)

# Create a Treeview widget for Modbus data
tree = ttk.Treeview(app, columns=("Description", "Address", "Value (16)", "Hex Value", "Binary Value", "Float (32)", "Conversion Type"))
tree.column("#1", width=150)
tree.column("#2", width=100)
tree.column("#3", width=100)
tree.column("#4", width=100)
tree.column("#5", width=150)
tree.column("#6", width=150)
tree.column("#7", width=150)

tree.heading("#1", text="Description")
tree.heading("#2", text="Address")
tree.heading("#3", text="Value (16)")
tree.heading("#4", text="Hex Value")
tree.heading("#5", text="Binary Value")
tree.heading("#6", text="DATA")
tree.heading("#7", text="Conversion Type")
tree.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

# Create a Treeview widget for communication traffic
communication_tree = ttk.Treeview(app, columns=("Direction", "Data"))
communication_tree.heading("#1", text="Direction")
communication_tree.heading("#2", text="Data")
communication_tree.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

# Function to clear input fields
def clear_input_fields():
    slave_id_var.set("")
    function_code_var.set("")
    starting_address_var.set("")
    quantity_var.set("")
    tcp_ip_var.set("")
    tcp_port_var.set("")

# Create a button to clear input fields
clear_input_button = ttk.Button(input_frame, text="Clear Input Fields", command=clear_input_fields)
clear_input_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

# Function to update Modbus Connection Status
def update_connection_status(status):
    connection_status_var.set(f"Modbus Connection: {status}")

# Function to read Modbus data
def read_data():
    TCP_IP = tcp_ip_var.get()
    TCP_PORT = int(tcp_port_var.get())

    slave_id = int(slave_id_var.get())
    function_code = int(function_code_var.get())
    starting_address = int(starting_address_var.get())
    quantity = int(quantity_var.get())

    message = bytearray([slave_id, function_code, starting_address >> 8, starting_address & 0xff, quantity >> 8, quantity & 0xff])
    crc = computeCRC(message)
    message += crc.to_bytes(2, byteorder='big')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((TCP_IP, TCP_PORT))
        update_connection_status("Connected")
        sock.send(message)

        response = sock.recv(1024)

        data = response[3:]
        data_type = data_type_var.get()

        if data_type == "32-bit":
            values = [int.from_bytes(data[i:i+4], byteorder='big') for i in range(0, len(data), 4)]
        elif data_type == "16-bit":
            values = [int.from_bytes(data[i:i+2], byteorder='big') for i in range(0, len(data), 2)]
        else:
            values = []

        sock.close()

        data_list = []
        for i, value in enumerate(values):
            address = starting_address + i
            data_list.append({'description': f'Description {i}', 'value': value, 'address': address, 'hex_value': f'0x{value:0X}', 'binary_value': f'{value:016b}', 'float_value': float(value), 'conversion_type': data_type})

        communication_traffic = [{'direction': 'TX', 'data': 'Command: Read Registers'},
                                {'direction': 'RX', 'data': 'Response: Data1=100, Data2=200, Data3=300'}]

        # Populate the Treeviews with data
        populate_tree(data_list)
        populate_communication_tree(communication_traffic)
       
    except Exception as e:
        update_connection_status("Not Connected")

# Function to populate the Treeview with Modbus data
def populate_tree(data_list):
    # Clear existing data
    tree.delete(*tree.get_children())

    # Insert data into the Treeview
    for data in data_list:
        tree.insert("", "end", values=(
            data['description'],
            data['address'],
            data['value'],
            data['hex_value'],
            data['binary_value'],
            data['float_value'],
            data['conversion_type']
        ))

# Function to populate the communication Treeview
def populate_communication_tree(communication_traffic):
    # Clear existing data
    communication_tree.delete(*communication_tree.get_children())

    # Insert data into the communication Treeview
    for data in communication_traffic:
        communication_tree.insert("", "end", values=(data['direction'], data['data']))

# Create a button to trigger data reading
read_button = ttk.Button(input_frame, text="Read Data", command=read_data)
read_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

# Configure grid row and column weights to make the UI expandable
app.grid_rowconfigure(2, weight=1)
app.grid_columnconfigure(0, weight=1)

# Start the Tkinter main loop
app.mainloop()


