import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta


class Exam:
    def __init__(self, date, start_time, duration, capacity):
        self.date = date
        self.start_time = start_time
        self.duration = duration
        self.capacity = capacity

    def __str__(self):
        return f"The exam is scheduled for {self.date} starting at {self.start_time} and lasts {self.duration} hours. This exam can accommodate {self.capacity} students."

    
class Course:
    def __init__(self, name):
        self.name = name
        self.groups_of_students = set()  # Groups of students taking this course
        self.num_of_students = 0

    def add_students(self, students_group, number_of_students):
        self.groups_of_students.add(students_group) 
        self.num_of_students += number_of_students

    def __str__(self):
        return f"Course: {self.name}"


class Students:
    def __init__(self, name, number_of_students):
        self.name = name
        self.num_of_students = number_of_students
        self.courses = []

    def add_course(self, course):
        self.courses.append(course)
        course.add_students(self, self.num_of_students)

    def __str__(self):
        return f"{self.name} - There are {self.num_of_students} students"

def solve_exam_scheduling(courses, slots, students):
    try:
        model = gp.Model()
        
        # Decision variables
        X = {}
        for course in courses:
            for slot in slots:
                var_name = f"X[{course.name}, {slot.date}, {slot.start_time}]"
                X[course, slot] = model.addVar(vtype=GRB.BINARY, name=var_name)
                
        # Objective function
        model.setObjective(0, sense=GRB.MINIMIZE)
        
        # Hard constraints
        
        # Constraint 1: Each course should be assigned to exactly one exam slot
        for course in courses:
            model.addConstr(gp.quicksum(X[course, slot] for slot in slots) == 1)
        
        # Constraint 2: Courses sharing a common group cannot be assigned to the same exam slot
        for i in range(len(courses)):
            for j in range(i+1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]
                if bool(course1.groups_of_students & course2.groups_of_students):
                    for slot in slots:
                        model.addConstr(X[course1, slot] + X[course2, slot] <= 1)
        
        def slots_overlap(slot1, slot2):
            if slot1.date == slot2.date:
                if not (is_exam_finished(slot1, slot2) or is_exam_finished(slot2, slot1)):
                    return True
            return False
        
        def is_exam_finished(slot1, exam2):
            exam1_end_time = get_start_time(slot1) + parse_duration(slot1.duration)
            exam2_start_time = get_start_time(exam2)
            return exam1_end_time <= exam2_start_time
        
        def get_start_time(slot):
            return parse_time(slot.start_time)
        
        def parse_time(time_string):
            hours, minutes = time_string.split(":")
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            return hours * 60 + minutes
        
        def parse_duration(duration_string):
            hours, minutes = duration_string.split("h")
            hours = int(hours.strip()) if hours else 0
            minutes = int(minutes.strip().replace("m", "")) if minutes else 0
            return int(hours) * 60 + int(minutes)
        
        # Constraint 3: Two courses sharing a group cannot be assigned to overlapping exam slots
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]
                if bool(course1.groups_of_students & course2.groups_of_students):
                    for m in range(len(slots)):
                        for n in range(m + 1, len(slots)):
                            slot1 = slots[m]
                            slot2 = slots[n]
                            if slot1.date == slot2.date and slots_overlap(slot1, slot2):
                                model.addConstr(X[course1, slot1] + X[course2, slot2] <= 0)
        
        # Constraint 4: Capacity constraint for each exam slot
        for course in courses:
            for slot in slots:
                if course.num_of_students > slot.capacity:
                    model.addConstr(X[course, slot] == 0)

        # Light constraints
        # We prefer schedules where two courses sharing a group do not have exams on same day 
        # example: exam on 03.03. stating at 08:00 and exam on same date starting at 13:00

        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]
                if bool(course1.groups_of_students & course2.groups_of_students):
                    for m in range(len(slots)):
                        for n in range(m + 1, len(slots)):
                            slot1 = slots[m]
                            slot2 = slots[n]
                            if slot1.date == slot2.date and not slots_overlap(slot1, slot2):
                                model.addConstr(
                                    X[course1, slot1] + X[course2, slot2] <= 1,
                                    f'LightConstraint_{course1.name}_{course2.name}_{slot1.date}_{slot1.start_time}_{slot2.date}_{slot2.start_time}'
                                )

        def are_days_consecutive(date1, date2):
            delta = timedelta(days=1)
            return (date2 - date1) == delta
        
        # # We prefer schedules where two courses sharing a group do not have exams on consecutive days
        # # example: exam on 03.03. and exam on 04.03. 

        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]
                if bool(course1.groups_of_students & course2.groups_of_students):
                    for m in range(len(slots)):
                        for n in range(m + 1, len(slots)):
                            slot1 = slots[m]
                            slot2 = slots[n]
                            if slot1.date != slot2.date and are_days_consecutive(slot1.date, slot2.date):
                                model.addConstr(
                                    X[course1, slot1] + X[course2, slot2] <= 1,
                                    f'LightConstraint_{course1.name}_{course2.name}_{slot1.date}_{slot1.start_time}_{slot2.date}_{slot2.start_time}'
                                )
        
        # Solve the model
        model.optimize()
        
        # Retrieve the solution
        schedule = {}
        for course in courses:
            for slot in slots:
                if X[course, slot].x == 1:
                    schedule[course] = slot
                    break
            else:
                schedule[course] = None
        
        return schedule
    
    except gp.GurobiError as e:
        print("Error: " + str(e))
        return None