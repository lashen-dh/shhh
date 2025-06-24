from ._anvil_designer import QuizTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import random

#TODO: Make it so that the questions chosen match student ELO
class Question():
  def __init__(self, strType, strInstruction, strDetails, strAnswers, strCorrectAnswer, intElo):
    self.dictDetails = { 'intElo': intElo, 'strType': strType, 'strInstruction': strInstruction, 'strDetails': strDetails, 'strAnswers': strAnswers, 'strInstruction': strInstruction, 'strCorrectAnswer': strCorrectAnswer, 'arrAnswers': strAnswers.split(",") }
    
class Quiz(QuizTemplate):
  def assignToButtons(self, question):
    #Display random order for button questions
    arrAnswerButtons, arrAlreadyChosenAnswers = [[self.btnAns1, self.btnAns2, self.btnAns3, self.btnAns4], []]
    strChosenAnswer = question.dictDetails['arrAnswers'][random.randint(0, 3)]
    
    for btnAnswer in arrAnswerButtons:
      #Keep choosing a random answer until we find one we haven't already put on a button
      while strChosenAnswer in arrAlreadyChosenAnswers:
        strChosenAnswer = question.dictDetails['arrAnswers'][random.randint(0, 3)]
      arrAlreadyChosenAnswers.append(strChosenAnswer)
      btnAnswer.text = strChosenAnswer
    
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
    #Choose a random index for random question
    arrQuestionQueue = []
    intChosenQuestionIndex = random.randint(0, self.quizData['intMaxNumberOfQuestions'] - 1)
    for intQuestionIndex in range(self.quizData['intMaxNumberOfQuestions']):
      while intChosenQuestionIndex in [key[0] for key in arrQuestionQueue]: #If the question selected already has been displayed, we keep looping until we get an index that hasn't been chosen before 
        intChosenQuestionIndex = random.randint(0, self.quizData['intMaxNumberOfQuestions'] - 1) #We subtract one from intMaxNumberOfQuestions since the array indexes start at zero, while the intMaxNumberOfQuestions starts at 1
      #Now that we've chosen an index that hasn't been chosen before, store it into the already chosen array to prvent it being selected again later
      chosenQuestionDatabaseReference = self.quizData['tblQuestions'][intChosenQuestionIndex]  
      #Add a question to the question queue with a new Question object created using database data for that respective question
      arrQuestionQueue.append((intChosenQuestionIndex, Question(chosenQuestionDatabaseReference['type'], chosenQuestionDatabaseReference['instruction'], chosenQuestionDatabaseReference['details'], chosenQuestionDatabaseReference['answers'], chosenQuestionDatabaseReference['correctAnswer'], chosenQuestionDatabaseReference['elo'])))
    return arrQuestionQueue
    
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

    #Delete every column in the question
    for column in currentQuestionInDatabase: 
      column.delete()

    #Add question back with updated values
    app_tables.tblquestions.add_row(type=self.quizData['currentQuestion'].dictDetails['strType'], instruction=self.quizData['currentQuestion'].dictDetails['strInstruction'], details=self.quizData['currentQuestion'].dictDetails['strDetails'], answers=self.quizData['currentQuestion'].dictDetails['strAnswers'], correctAnswer=self.quizData['currentQuestion'].dictDetails['strCorrectAnswer'], elo=self.quizData['currentQuestion'].dictDetails['intElo'])
    
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

  def btnAns1_click(self, **event_args):
    self.quizData['intSelectedButton'] = 0
    self.btnAns1.appearance, self.btnAns2.appearance, self.btnAns3.appearance, self.btnAns4.appearance = ["filled", "outlined", "outlined", "outlined"]

  def btnAns2_click(self, **event_args):
    self.quizData['intSelectedButton'] = 1
    self.btnAns1.appearance, self.btnAns2.appearance, self.btnAns3.appearance, self.btnAns4.appearance = ["outlined", "filled", "outlined", "outlined"]
    
  def btnAns3_click(self, **event_args):
    self.quizData['intSelectedButton'] = 2
    self.btnAns1.appearance, self.btnAns2.appearance, self.btnAns3.appearance, self.btnAns4.appearance = ["outlined", "outlined", "filled", "outlined"]

  def btnAns4_click(self, **event_args):
    self.quizData['intSelectedButton'] = 3
    self.btnAns1.appearance, self.btnAns2.appearance, self.btnAns3.appearance, self.btnAns4.appearance = ["outlined", "outlined", "outlined", "filled"]