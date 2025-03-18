import pandas as pd
import numpy as np
import sqlite3

def get_attendance_file(file_path):
    data = pd.read_csv(file_path)
    data.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
    data.dropna(inplace=True)
    return data

def calculate_attendance_percentage(data,attendance_columns,column_name):
    attendance = ((
        (data[attendance_columns] == 'P').sum(axis=1) / len(attendance_columns)
    ) * 100).round()
    data.loc[:, column_name] = attendance
    return data

def get_leave_file():
    conn = sqlite3.connect('database1.db')

    query = '''SELECT students.name, students.usn, leaves.from_date, leaves.to_date
    FROM leaves
    JOIN students ON leaves.student_id = students.id
    WHERE leaves.status = 'Approved';
    '''

    leave_data = pd.read_sql_query(query, conn)
    conn.close()
    leave_data.to_csv('csv/leaves/leaves1.csv', index= False)
    return leave_data

def update_attendance_with_leaves(data, leave_data):
    attendance_columns = data.columns[2:] 
    for index, row in leave_data.iterrows():
        usn = row['usn']
        from_date = pd.to_datetime(row['from_date'])
        to_date = pd.to_datetime(row['to_date'])

        leave_dates = pd.date_range(start=from_date, end=to_date).strftime('%d-%m-%Y')
        
        if usn in data['USN'].values:
            for date in leave_dates:
                if date in attendance_columns:
                    data.loc[data['USN'] == usn, date] = 'P'
    return data

def calculate_fine(attendance_percentage):
    if attendance_percentage >= 85:
        return 0
    else:
        fine = np.ceil((85 - attendance_percentage) / 5) * 100
        return fine

def apply_fines(data):
    data['Fine'] = data['Attendance percentage'].apply(calculate_fine)
    return data

def main(file_path):

    data = get_attendance_file(file_path)

    leave_data = get_leave_file()

    data = update_attendance_with_leaves(data, leave_data)

    attendance_columns = data.columns[2:] 
    data = calculate_attendance_percentage(data,attendance_columns,'Attendance percentage')

    data = apply_fines(data)

    fines =  data[['USN','Student_name','Attendance percentage', 'Fine']]
    
    return fines

def merge(subject_files):

    consolidated_data = pd.DataFrame()

    for subject_file in subject_files:
        subject_data = pd.read_csv(subject_file['file'])
        subject_data.rename(columns={'Fine': subject_file['subject']}, inplace=True)  # Rename fine column to subject
        if consolidated_data.empty:
            consolidated_data = subject_data
        else:
            print(consolidated_data)
            consolidated_data = pd.merge(consolidated_data, subject_data[['USN','Attendance percentage', subject_file['subject']]], on='USN', how='outer')

    # Fill missing fine values with 0
    consolidated_data.fillna(0, inplace=True)

    # Calculate grand total fine
    fine_columns = [subject_file['subject'] for subject_file in subject_files]
    consolidated_data['Grand Total Fine'] = consolidated_data[fine_columns].sum(axis=1)
    return consolidated_data
