from utils import main

file_path =  'csv/attendance/attend_data.csv'

fines_csv = main(file_path=file_path)

fines_csv.to_csv('csv/fines/fines_csv.csv',index = False)






""""
    low_attendance_students = filter_low_attendance_students(data)

    leave_data = get_leave_file()

    low_attendance_students = update_attendance_with_leaves(low_attendance_students, leave_data)

    attendance_columns = low_attendance_students.columns[2:-1] 
    low_attendance_students = calculate_attendance_percentage(low_attendance_students,attendance_columns,'Updated Attendance percentage')

    low_attendance_students = apply_fines(low_attendance_students)

    fines =  low_attendance_students[['USN','Student_name','Updated Attendance percentage', 'fine']]
"""