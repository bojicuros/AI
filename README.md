
# AI project

## Starting program:

with open('Instance/instance_name.pickle', 'rb') as file:
        data = pickle.load(file)

exams = data['exams']
courses = data['courses']
students = data['students']

- If you want to start Iterated Local Search:

exam_schedule = ExamScheduleILS(exams,courses,students)
result = exam_schedule.find_schedule()

- If you want to start Genetic Algoritm:

exam_schedule = GeneticAlgorithm(exams,courses,students)
result = exam_schedule.run()

- If you want to start Gurobi:

solve_exam_scheduling(courses, exams ,students)
