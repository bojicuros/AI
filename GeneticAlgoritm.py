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
    

class GeneticAlgorithm:
    POPULATION_SIZE = 100
    NUMBER_OF_GENERATIONS = 50
    CROSSOVER_RATE = 0.8
    MUTATION_RATE = 0.2

    HARD_CONSTRAINT_PENALTY = 100000
    LIGHT_CONSTRAINT_PENALTY = 100
    START_TIME_FACTOR = 0

    def __init__(self, exams, courses, students):
        self.exams = exams
        self.courses = courses
        self.students = students

    def run(self):
        population = self.initialize_population()

        for generation in range(GeneticAlgorithm.NUMBER_OF_GENERATIONS):
            population = self.selection(population)
            population = self.crossover(population)
            self.mutation(population)

        best_schedule = self.get_best_schedule(population)
        return best_schedule

    def initialize_population(self):
        population = []
        schedule = self.find_initial_schedule()

        for _ in range(GeneticAlgorithm.POPULATION_SIZE):
            member = self.generate_candidate(schedule)
            population.append(member)

        return population

    def generate_candidate(self, current_schedule):
        candidate_schedule = copy.deepcopy(current_schedule)

        course = random.choice(list(candidate_schedule.keys()))
        exam = random.choice(self.exams)
        
        candidate_schedule[course] = exam

        return candidate_schedule

    def selection(self, population):
        sorted_population = sorted(population, key=lambda x: self.calculate_schedule_fitness(x))
        elite_size = int(GeneticAlgorithm.POPULATION_SIZE * 0.2)  # Select the top 20% as elite individuals
        elite = sorted_population[:elite_size]
        
        return elite

    def crossover(self, population):
        new_population = population.copy()
        
        while len(new_population) < GeneticAlgorithm.POPULATION_SIZE:
            parent1 = random.choice(population)
            parent2 = random.choice(population)

            if random.random() < GeneticAlgorithm.CROSSOVER_RATE:
                offspring = self.perform_crossover(parent1, parent2)
                new_population.append(offspring)

        return new_population

    def perform_crossover(self, parent1, parent2):  # simple one-point crossover

        offspring = {}

        crossover_point = random.randint(1, len(self.courses))
        parent1_courses = list(parent1.keys())
        parent2_courses = list(parent2.keys())

        for i in range(len(self.courses)):
            course = self.courses[i]

            if i < crossover_point:
                offspring[course] = parent1[parent1_courses[i]]
            else:
                offspring[course] = parent2[parent2_courses[i]]

        return offspring

    def mutation(self, population):
        for schedule in population:
            if random.random() < GeneticAlgorithm.MUTATION_RATE:
                self.perform_mutation(schedule)


    def perform_mutation(self, schedule):
        courses = list(schedule.keys())

        mutation_courses = random.sample(courses, k=random.randint(1, len(courses)))

        for course in mutation_courses:
            if random.random() < GeneticAlgorithm.MUTATION_RATE:
                exam = random.choice(self.exams)
                schedule[course] = exam


    def get_best_schedule(self, population):
        best_fitness = float('inf')
        best_schedule = None

        for schedule in population:
            fitness = self.calculate_schedule_fitness(schedule)
            if fitness < best_fitness:
                best_fitness = fitness
                best_schedule = schedule

        return best_schedule
    
    def calculate_schedule_fitness(self, schedule):
        fitness = 0
                
        for course, exam in schedule.items():
            if exam is None:
                fitness += GeneticAlgorithm.HARD_CONSTRAINT_PENALTY - GeneticAlgorithm.LIGHT_CONSTRAINT_PENALTY
                continue
                
            fitness += self.calculate_exam_fitness(exam)
        
            if exam.capacity < course.num_of_students:
                fitness += GeneticAlgorithm.HARD_CONSTRAINT_PENALTY
                        
            if self.conflicts_exist(schedule, exam, course):
                fitness += GeneticAlgorithm.HARD_CONSTRAINT_PENALTY

            if self.has_consecutive_days(schedule, exam, course):
                fitness += GeneticAlgorithm.LIGHT_CONSTRAINT_PENALTY

            if self.same_day_different_time(schedule, exam, course):
                fitness += GeneticAlgorithm.LIGHT_CONSTRAINT_PENALTY * 2
        
        return fitness

    
    def calculate_exam_fitness(self, exam):
        fitness = 0

        start_time = self.get_start_time(exam)
        fitness = GeneticAlgorithm.START_TIME_FACTOR * start_time
        
        return fitness

    
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
    
    def is_acceptable(self, exam, course):
        if exam.capacity < course.num_of_students:
            return False
        return True
    
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
    
    def conflicts_exist(self, schedule, exam, course):
        first_same = True
        for other_course, other_exam in schedule.items():
            if other_exam is None:
                continue
            elif other_exam == exam and first_same:
                first_same = False
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