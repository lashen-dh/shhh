from ._anvil_designer import QuizTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import random

#TODO: Make it so that the questions chosen match student ELO
class Question():
  def __init__(self, strType, strInstruction, strDetails, strAnswers, strCorrectAnswer, intElo):
    self.dictDetails = { 'intElo': intElo, 'strType': strType, 'strInstruction': strInstruction, 'strDetails': strDetails, 'strAnswers': strAnswers, 'strCorrectAnswer': strCorrectAnswer, 'arrAnswers': strAnswers.split(",") }
    
class Quiz(QuizTemplate):
  def assignToButtons(self, question):
    #Display random order for button questions
    arrAnswerButtons = [self.btnAns1, self.btnAns2, self.btnAns3, self.btnAns4]
    random.shuffle(question.dictDetails['arrAnswers'])
    for i, btn in enumerate(arrAnswerButtons):
      btn.text = question.dictDetails['arrAnswers'][i]
    
  def displayQuestion(self, num):
    self.lblQuestionNumber.text = f"Question Number {self.quizData['intQuestionNumber'] + 1}/{self.quizData['intMaxNumberOfQuestions']}"
    newQuestion = self.arrQuestionQueue[num][1]
    self.lblQuestionInstruction.text, self.lblQuestionDetails.text = newQuestion.dictDetails['strInstruction'], newQuestion.dictDetails['strDetails']
    self.assignToButtons(self.arrQuestionQueue[num][1])
    return newQuestion
  
  def nextQuestion(self):
    if self.quizData['intQuestionNumber'] >= self.quizData['intMaxNumberOfQuestions'] - 1:
      open_form('ResultsPage')
      return None
    self.quizData['intQuestionNumber'] += 1
    return self.displayQuestion(self.quizData['intQuestionNumber'])

  def setupQuestionQueue(self):
    # Create a list of tuples where each tuple contains (index, Question object)
    arrQuestions = [
      (i, Question(
        q['type'], q['instruction'], q['details'], q['answers'], q['correctAnswer'], q['elo']
      )) for i, q in enumerate(self.quizData['tblQuestions'])
    ]

    # Sort the list of questions by the absolute difference between the student's Elo and the question's Elo
    arrQuestions.sort(key=lambda x: abs(x[1].dictDetails['intElo'] - self.quizData['intStudentElo']))

    # Return the sorted list
    return arrQuestions
    
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.intTime = {"minutes": 0, "seconds": 0}
    self.quizData = { "intMaxNumberOfQuestions": 5, "intQuestionNumber": 0, "intStudentElo": 1500, "intSelectedButton": 0, 'tblQuestions': app_tables.tblquestions.search() }
    self.lblScore.text = self.quizData['intStudentElo']
    #If we want 20 questions in a test, but there is less than 20 available in database, give us the number in the database
    self.quizData['intMaxNumberOfQuestions'] = len(self.quizData['tblQuestions']) if self.quizData['intMaxNumberOfQuestions'] > len(self.quizData['tblQuestions']) else self.quizData['intMaxNumberOfQuestions']

    self.arrQuestionQueue = self.setupQuestionQueue() #Setup the queue
    #Now that we've set up the question queue, display the first question out that queue
    self.quizData['currentQuestion'] = self.displayQuestion(0) #Add current question to our quiz data
    #Initialization has been finished
    
  def timer_tick(self, **event_args):
    self.intTime['seconds'] += 1
    if self.intTime['seconds'] >= 60:
      self.intTime['minutes'] += 1
      self.intTime['seconds'] -= 60
    self.lblTimeTaken.text = f"Time Taken: {self.intTime['minutes']}:{self.intTime['seconds']:02d}"

  def eloChange(self, correct, **event_args):
    print(correct)
    #ELO calculation
    k = 32
    floatExpectedStudentScore = 1 / (1 + 10**((self.quizData['currentQuestion'].dictDetails['intElo'] - self.quizData['intStudentElo']) / 400))
    floatActualScore = correct
    floatEloDelta = round(k * (floatActualScore - floatExpectedStudentScore), 2)
  
    self.quizData['intStudentElo'] += floatEloDelta
    self.quizData['currentQuestion'].dictDetails['intElo'] -= floatEloDelta
    self.lblScore.text = self.quizData['intStudentElo']
    
    #Remove question from database, first searching it up and gaining reference to it within the table
    currentQuestionInDatabase = app_tables.tblquestions.search(type=self.quizData['currentQuestion'].dictDetails['strType'], instruction=self.quizData['currentQuestion'].dictDetails['strInstruction'], details=self.quizData['currentQuestion'].dictDetails['strDetails'])
    currentQuestionInDatabase[0].update(elo=self.quizData['currentQuestion'].dictDetails['intElo'])
    
  def btnSubmit_click(self, **event_args):
    #Multiple Choice Question
    if(self.quizData['currentQuestion'].dictDetails['strType'].lower() == "mc"):
      if(self.quizData['currentQuestion'].dictDetails['arrAnswers'][self.quizData['intSelectedButton']] == self.quizData['currentQuestion'].dictDetails['strCorrectAnswer']):
        self.eloChange(1)
      else:
        self.eloChange(0)

      if(self.quizData['intQuestionNumber'] < self.quizData['intMaxNumberOfQuestions'] - 1):
        self.quizData['currentQuestion'] = self.nextQuestion()
      else:
        open_form('ResultsPage')

  def toggleAnswerButton(self, index, **event_args):
    self.quizData['intSelectedButton'] = index
    buttons = [self.btnAns1, self.btnAns2, self.btnAns3, self.btnAns4]
    for i, btn in enumerate(buttons):
      btn.appearance = "filled" if i == index else "outlined"

  def btnAns1_click(self, **event_args):
    self.toggleAnswerButton(0)

  def btnAns2_click(self, **event_args):
    self.toggleAnswerButton(1)

  def btnAns3_click(self, **event_args):
    self.toggleAnswerButton(2)

  def btnAns4_click(self, **event_args):
    self.toggleAnswerButton(3)