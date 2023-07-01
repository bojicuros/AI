import datetime
from datetime import date, timedelta
import random
import copy

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
    
class ExamScheduleILS:
    
    NUMBER_OF_ITERATIONS = 50
    HARD_CONSTRAINT_PENALTY = 100000
    LIGHT_CONSTRAINT_PENALTY = 100
    START_TIME_FACTOR = 0

    def __init__(self, exams, courses, students):
        self.exams = exams
        self.courses = courses
        self.students = students
        
    def find_schedule(self):
        best_schedule = self.find_initial_schedule()
        best_fitness = self.calculate_schedule_fitness(best_schedule)
    
        for _ in range(ExamScheduleILS.NUMBER_OF_ITERATIONS):
            
            candidate_schedule = self.generate_candidate(best_schedule)
            
            improved_schedule = self.local_search(candidate_schedule)
            potential_best = self.calculate_schedule_fitness(improved_schedule)
                        
            if potential_best < best_fitness:
                best_fitness = potential_best
                best_schedule = improved_schedule

        return best_schedule
    
    def find_initial_schedule(self):
        schedule = {}

        for course in self.courses:
            found = False
            for exam in self.exams:   

                if not self.is_acceptable(exam, course):
                    continue

                if self.no_conflicts(exam, course, schedule):
                    schedule[course] = exam
                    found = True
                    break
                                        
                if self.on_consecutive_days(exam, course, schedule):
                    schedule[course] = exam
                    found = True
                    break
                                                            
                if self.can_schedule_exam(exam, course, schedule):
                    schedule[course] = exam
                    found = True
                    break
                
            if not found:    
                schedule[course] = None

        return schedule   

    def generate_candidate(self, current_schedule):
        candidate_schedule = copy.deepcopy(current_schedule)

        course = random.choice(list(candidate_schedule.keys()))

        new_exam = random.choice(self.exams)

        candidate_schedule[course] = new_exam

        return candidate_schedule

    def local_search(self, initial_schedule):
        best_schedule = initial_schedule
        best_fitness = self.calculate_schedule_fitness(best_schedule)

        for _ in range(ExamScheduleILS.NUMBER_OF_ITERATIONS):
            neighbors = self.generate_neighbors(best_schedule)
            if not neighbors:
                break
            
            neighbor = random.choice(neighbors)
            neighbor_fitness = self.calculate_schedule_fitness(neighbor)

            if neighbor_fitness < best_fitness:
                best_schedule = neighbor
                best_fitness = neighbor_fitness

        return best_schedule

    def generate_neighbors(self, schedule):
        neighbors = []

        for course1, exam1 in schedule.items():
            if exam1 is None:
                continue

            for course2, exam2 in schedule.items():
                if exam2 is None or course1 == course2:
                    continue

                neighbor = schedule.copy()
                neighbor[course1], neighbor[course2] = exam2, exam1
                neighbors.append(neighbor)

        return neighbors


    def calculate_schedule_fitness(self, schedule):
        fitness = 0
                
        for course, exam in schedule.items():
            if exam is None:
                fitness += ExamScheduleILS.HARD_CONSTRAINT_PENALTY - ExamScheduleILS.LIGHT_CONSTRAINT_PENALTY
                continue
                
            fitness += self.calculate_exam_fitness(exam)
        
            if exam.capacity < course.num_of_students:
                fitness += ExamScheduleILS.HARD_CONSTRAINT_PENALTY
                        
            if self.conflicts_exist(schedule, exam, course):
                fitness += ExamScheduleILS.HARD_CONSTRAINT_PENALTY

            if self.has_consecutive_days(schedule, exam, course):
                fitness += ExamScheduleILS.LIGHT_CONSTRAINT_PENALTY

            if self.same_day_different_time(schedule, exam, course):
                fitness += ExamScheduleILS.LIGHT_CONSTRAINT_PENALTY * 2
        
        return fitness

    
    def calculate_exam_fitness(self, exam):
        fitness = 0

        start_time = self.get_start_time(exam)
        fitness = ExamScheduleILS.START_TIME_FACTOR * start_time
        
        return fitness
    
    def is_acceptable(self, exam, course):
        if exam.capacity < course.num_of_students:
            return False
        return True
    
    def conflicts_exist(self, schedule, exam, course):
        for other_course, other_exam in schedule.items():
            if other_exam is None or other_exam == exam:
                continue

            if self.together(other_course, course) and other_exam.date == exam.date and not (self.is_exam_finished(other_exam, exam) or self.is_exam_finished(exam, other_exam)):
                return True
        return False
    
    def has_consecutive_days(self, schedule, exam, course):
        for other_course, other_exam in schedule.items():
            if other_exam is None or other_exam == exam:
                continue

            if self.together(other_course, course) and self.are_days_consecutive(other_exam.date, exam.date):
                return True
        return False

    
    def same_day_different_time(self, schedule, exam, course):
        for other_course, other_exam in schedule.items():
            if other_exam is None or other_exam == exam:
                continue

            if self.together(other_course, course) and other_exam.date == exam.date and (self.is_exam_finished(other_exam, exam) or self.is_exam_finished(exam, other_exam)):
                return True

        return False


    def no_conflicts(self, exam, course, schedule):
        for c, e in schedule.items():
            if e is not None and self.together(course, c) and (e.date == exam.date or self.are_days_consecutive(e.date, exam.date)):
                return False
        return True
    
    def together(self, course1, course2):
        return bool(course1.groups_of_students & course2.groups_of_students)
    
    def are_days_consecutive(self, date1, date2):
        delta = datetime.timedelta(days=1)
        return (date2 - date1) == delta
    
    def on_consecutive_days(self, exam, course, schedule):
        for c, e in schedule.items():
            if e is not None and self.together(course, c) and e.date != exam.date:
                if self.are_days_consecutive(e.date, exam.date) and self.no_conflicts(exam, course, schedule):
                    return True
        return False
    
    def can_schedule_exam(self, exam, course, schedule):
        for given_course, scheduled_exam in schedule.items():
            if scheduled_exam is not None and self.together(course, given_course) and scheduled_exam.date == exam.date:
                if not (self.is_exam_finished(exam, scheduled_exam) or self.is_exam_finished(scheduled_exam, exam)):
                    return False
        return True

    def is_exam_finished(self, exam1, exam2):
        exam1_end_time = self.get_start_time(exam1) + self.parse_duration(exam1.duration)
        exam2_start_time = self.get_start_time(exam2)
        return exam1_end_time <= exam2_start_time

    def get_start_time(self, exam):
        return self.parse_time(exam.start_time)

    def parse_time(self, time_string):
        hours, minutes = time_string.split(":")
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        return hours * 60 + minutes

    def parse_duration(self, duration_string):
        hours, minutes = duration_string.split("h")
        hours = int(hours.strip()) if hours else 0
        minutes = int(minutes.strip().replace("m", "")) if minutes else 0
        return int(hours) * 60 + int(minutes)
    
def print_schedule(schedule):
    if schedule:
        print("Exam Schedule:")
        for course, exam in schedule.items():
            course_name = course.name
            if exam is not None:
                exam_date = exam.date
                exam_start_time = exam.start_time
                exam_duration = exam.duration
                print(f"{course_name} - {exam_date}, {exam_start_time}, {exam_duration}")
            else:
                print(f"{course_name} - No valid exam")
    else:
        print("Schedule could not be found")
