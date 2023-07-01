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


EXAMS_ON_SAME_DAY_PENALTY = 200
EXAMS_ON_CONCECUTIVE_DAYS_PENALTY = 100


def parse_duration(duration_string):
    hours, minutes = duration_string.split("h")
    hours = int(hours.strip()) if hours else 0
    minutes = int(minutes.strip().replace("m", "")) if minutes else 0
    return int(hours) * 60 + int(minutes)

def parse_time(time_string):
    hours, minutes = time_string.split(":")
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    return hours * 60 + minutes

def get_start_time(slot):
    return parse_time(slot.start_time)

def is_exam_finished(slot1, exam2):
            exam1_end_time = get_start_time(slot1) + parse_duration(slot1.duration)
            exam2_start_time = get_start_time(exam2)
            return exam1_end_time <= exam2_start_time


def slots_overlap(slot1, slot2):
            if slot1.date == slot2.date:
                if not (is_exam_finished(slot1, slot2) or is_exam_finished(slot2, slot1)):
                    return True
            return False

def same_day_conflict(course1, course2, slot1, slot2):
    if (
        bool(course1.groups_of_students & course2.groups_of_students)
        and slot1.date == slot2.date
        and not slots_overlap(slot1, slot2)
    ):
        print("same day",course1.name, course2.name,slot1.date, slot1.start_time,slot2.date, slot2.start_time)
        return 1
    return 0

def are_days_consecutive(date1, date2):
    delta = timedelta(days=1)
    return (date2 - date1) == delta

def consecutive_days_conflict(course1, course2, slot1, slot2):
    if (
        bool(course1.groups_of_students & course2.groups_of_students)
        and slot1.date != slot2.date
        and are_days_consecutive(slot1.date, slot2.date)
    ):
        print("consecutive days",course1.name, course2.name,slot1.date, slot1.start_time,slot2.date, slot2.start_time)
        return 1
    return 0


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
        model.setObjective(
            gp.quicksum(
                EXAMS_ON_SAME_DAY_PENALTY * X[courses[i], slots[m]] * X[courses[j], slots[n]] * same_day_conflict(courses[i], courses[j], slots[m], slots[n])
                for i in range(len(courses))
                for j in range(i + 1, len(courses))
                for m in range(len(slots))
                for n in range(m + 1, len(slots))
            ) + gp.quicksum(
                EXAMS_ON_CONCECUTIVE_DAYS_PENALTY * X[courses[i], slots[m]] * X[courses[j], slots[n]] * consecutive_days_conflict(courses[i], courses[j], slots[m], slots[n])
                for i in range(len(courses))
                for j in range(i + 1, len(courses))
                for m in range(len(slots))
                for n in range(m + 1, len(slots))
            ),
            sense=GRB.MINIMIZE,
        )

        # Hard constraints

        # Constraint 1: Each course should be assigned to exactly one exam slot
        for course in courses:
            model.addConstr(gp.quicksum(X[course, slot] for slot in slots) == 1)

        # Constraint 2: Courses sharing a common group cannot be assigned to the same exam slot
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]
                if bool(course1.groups_of_students & course2.groups_of_students):
                    for slot in slots:
                        model.addConstr(X[course1, slot] + X[course2, slot] <= 1)
        

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
                                model.addConstr(X[course1, slot1] + X[course2, slot2] <= 1)

        # Constraint 4: Capacity constraint for each exam slot
        for course in courses:
            for slot in slots:
                if course.num_of_students > slot.capacity:
                    model.addConstr(X[course, slot] == 0)

        model.optimize()

        # Retrieve the solution
        solution = {}
        for course in courses:
            for slot in slots:
                if X[course, slot].x > 0.5:
                    solution[course] = slot

        return solution

    except gp.GurobiError as e:
        print("Error code " + str(e.errno) + ": " + str(e))

    except AttributeError:
        print("Encountered an attribute error")