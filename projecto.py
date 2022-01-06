import salabim as sim
import math
import random

#///////////////////////////////////////////////////////////////////////////////////////////#
#                                          VARIABLES                                        #
#-Resources----------------------------------------------------------------------------------
# Simulation resources
nPress              = 4
nCutter             = 3
nFinisher           = 1
nPainter            = 1
nFoundry            = 1
nMachine            = 2
nPrinter            = 1
nPackingDecks       = 2
nPackingWheels      = 1
nSkateAssembler     = 2
nEndlineWorkers     = 2

#-Lots---------------------------------------------------------------------------------------
# How many are in a lot
nBoardLots          = 24
nWheelLots          = 192
nBoardBox           = 12
nWheelBox           = 48
nSkateLots          = 24

#-Times--------------------------------------------------------------------------------------
# How long it takes for each process to complete successfuly
timePressing        = 1.66  /nBoardLots
timeCutting         = 1     /nBoardLots
timeFinishing       = 0.25  /nBoardLots
timePainting        = (1/3)  /nBoardLots
timeFoundry         = 0.92  /nWheelLots
timeMachining       = 1     /nWheelLots
timePrinting        = (1/3)  /nWheelLots
timePackingDecks    = 0.17  /nBoardBox
timePackingWheels   = 0.5    /nWheelBox
timeAssemblyLine    = 0.5    /nSkateLots

#-Model Variables----------------------------------------------------------------------------
# Model specific amounts to test the simulation
deckAssemblyRate    = 60
wheelAssemblyRate   = 66
MODEL_boardLots     = 8800 / nBoardLots
MODEL_wheelLots     = 31680 / nWheelLots
MODEL_days          = 22

#-Timed hold for failstate-------------------------------------------------------------------
assembleFailWait    = 6
packDeckFailWait    = 6
packWheelFailWait   = 6

#-Timescales and Schedules-------------------------------------------------------------------
# Schedule is 10:00 to 18:00. After key steps, products are passed to the 
# storages that exist inbetween assembly lines
timeScale           = 1
fullDay             = 24 * timeScale
totalTime           = 24 * timeScale * MODEL_days
midnightWait        = 6 * timeScale
startTime           = 10 * timeScale #10AM Start
endTime             = 18 * timeScale #6PM End
nightWait           = midnightWait + startTime

#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                             STATISTICS                                    #
#-Stat Class---------------------------------------------------------------------------------
class SimulationStatistics(sim.Component):
    STAT_pressed         = 0
    STAT_cut             = 0
    STAT_finished        = 0
    STAT_painted         = 0
    STAT_forged          = 0
    STAT_machined        = 0
    STAT_printed         = 0
    STAT_packedWheels    = 0
    STAT_packedDecks     = 0
    STAT_packedSkates    = 0
    STAT_wheelToAssembly = 0
    STAT_deckToAssembly  = 0
    STAT_deckToPacking   = 0
    STAT_wheelToPacking  = 0
    
#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                       AUXILIARY                                           #
#-getCurrentDay helper-----------------------------------------------------------------------
currentDay=1
class getCurrentDay(sim.Component):
    def process(self):
        # set the current day divided by full day
        now = env.now()
        global currentDay
        currentDay = math.ceil(now/fullDay)+1
        
#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                         STORAGES                                          #
#-Storage1-----------------------------------------------------------------------------------
# Recieve boards fresh from pressing and wait for the next day to begin cutting
class Storage1(sim.Component):
    def process(self):
        # wait until the next day's start
        yield self.hold(nightWait)
        Cut()
        
#-Storage2-----------------------------------------------------------------------------------
# Recieve boards fresh from finishing the second phase and send them to the
# deciding structure
class Storage2(sim.Component):
    def process(self):
        # wait until the next day's start
        yield self.hold(nightWait)
        BranchBoards()
        
#-Storage3-----------------------------------------------------------------------------------
# Recieve boards fresh from the foundry and wait for the next day to machine        
class Storage3(sim.Component):
    def process(self):
        # wait until the next day's start
        yield self.hold(nightWait)
        Machine()
        
#-Storage4-----------------------------------------------------------------------------------
# Recieve wheels fresh from finishing the second phase and send them to the
# deciding structure
class Storage4(sim.Component):
    def process(self):
        # wait until the next day's start
        yield self.hold(nightWait)
        BranchWheels()

#-Final Storage------------------------------------------------------------------------------
# Recieves product from last stages for assembly/packing
class finalStorage(sim.Component):
    nDecks          = 0
    nWheels         = 0  
    packedDecks     = 0
    packedWheels    = 0
    packedSkates    = 0
    
#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                          Factory Class                                    #
#-Factory------------------------------------------------------------------------------------
class Factory(sim.Component):
    def setup(self, boards, wheels):
        self.boards = boards
        self.wheels = wheels
    def process(self):
        while self.boards > 0:     
            self.boards -= 1
            BoardStartup()
                 
        while self.wheels > 0:               
            self.wheels -= 1
            WheelStartup()
            
#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                       Board Processing                                    #
#-Initiator----------------------------------------------------------------------------------
class BoardStartup(sim.Component):
    def process(self):
        time = env.now()
        yield self.hold(startTime - time) #factory opens at 10
        Press()
     
#-Press--------------------------------------------------------------------------------------
class Press(sim.Component):
    def process(self):
                         
        
        # Enter queue
        self.enter(pressQueue)
        yield self.request((press, 1))
        
        
        # Verify if there is enough time on the day to press
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timePressing:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
       
        
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed+1)+" -> ENTERED PRESSING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")

        # Leave the queue, do the work, and release the worker
        self.leave(pressQueue)
        yield self.hold(timePressing)
        self.release((press, 1))
        # Wait until the endtime
        currentTime = env.now()
        currentTime = math.floor(currentTime)
        getCurrentDay()
        yield self.hold((currentDay*fullDay)-midnightWait-currentTime)
        
        
        # Update statistics
        SimulationStatistics.STAT_pressed+=1
        Storage1()
         
#-Cutter-------------------------------------------------------------------------------------
class Cut(sim.Component):
    def process(self):                 
        
        
        # Enter queue
        self.enter(cuttingQueue)
        yield self.request((cutter, 1))
        
        
        # Verify if there is enough time on the day to cut
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timeCutting:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
        
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_cut+1)+" -> ENTERED CUTTING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        # Leave the queue, do the work, and release the worker
        self.leave(cuttingQueue)
        yield self.hold(timeCutting)
        self.release((cutter, 1))
        # No wait till 18.. Not here!
        
        
        # Update statistics
        SimulationStatistics.STAT_cut+=1
        Finish()
        
#-Finisher-----------------------------------------------------------------------------------
class Finish(sim.Component):
    def process(self):
                         
        
        # Enter queue
        self.enter(finishingQueue)
        yield self.request((finisher, 1))
    
    
        # Verify if there is enough time on the day to finish
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timeFinishing:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
            
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_finished+1)+" -> ENTERED FINISHING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        # Leave the queue, do the work, and release the worker
        self.leave(finishingQueue)
        yield self.hold(timeFinishing)
        self.release((finisher, 1))
        # No wait till 18.. Not here!
        
        
        # Update statistics
        SimulationStatistics.STAT_finished+=1
        Paint()  
        
 #-Painter-----------------------------------------------------------------------------------
class Paint(sim.Component):
    def process(self):
                         
        
        # Enter queue
        self.enter(paintingQueue)
        yield self.request((painter, 1))
        
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timePainting:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)


        # Printing
#        currentTime = env.now()
#        getCurrentDay()            
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_painted+1)+" -> ENTERED PAINTING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        
        # Leave the queue, do the work, and release the worker
        self.leave(paintingQueue)
        yield self.hold(timePainting)
        self.release((painter, 1))
        # Wait until the endtime
        currentTime = math.floor(env.now())
        getCurrentDay()
        yield self.hold((currentDay*fullDay)-midnightWait-currentTime)
        
        
        # Update Statistics
        SimulationStatistics.STAT_painted+=1
        Storage2()  

#-Brancher-----------------------------------------------------------------------------------
class BranchBoards(sim.Component):
    def process(self):
        decision = random.randint(0, 100)
        finalStorage.nDecks+=1
        if (decision < deckAssemblyRate):
            if (finalStorage.nWheels>3 and finalStorage.nDecks>0):
                Assemble()
        else:
            if finalStorage.nDecks>=8:
                PackDecks()
          
#-PackDecks----------------------------------------------------------------------------------
class PackDecks(sim.Component):
    def process(self):
        
        # Semaphore checking (sim states)
        updateStates()
        yield self.wait(packDeckAllowed, fail_delay = packDeckFailWait)
        finalStorage.nDecks -= 8
        SimulationStatistics.STAT_deckToPacking+=8
        
        
        # Enter queue
        self.enter(packingDecksQueue)
        yield self.request((deckPacker,1))
            
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = math.ceil(currentDay*fullDay-midnightWait-currentTime)
        if remaining < timePackingDecks:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
        
        
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED DECK PACKING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        
        # Leave the queue, do the work, and release the worker
        self.leave(packingDecksQueue)
        yield self.hold(timePackingDecks)
        self.release((deckPacker,1))
        # No waiting here
        
        
        # Update statistics
        SimulationStatistics.STAT_packedDecks+=1
        finalStorage.packedDecks+=1
        
#///////////////////////////////////////////////////////////////////////////////////////////#















#///////////////////////////////////////////////////////////////////////////////////////////#
#                                   WHEEL PROCESSING                                        #
#-Wheel starter------------------------------------------------------------------------------
class WheelStartup(sim.Component):
    def process(self):
        time = env.now()
        yield self.hold(startTime - time) #factory opens at 10
        Smelt()
        
#-Smelter/Foundry----------------------------------------------------------------------------
class Smelt(sim.Component):
    def process(self):
                         
        
        # Enter queue
        self.enter(foundryQueue)
        yield self.request((foundry, 1))
        
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timeFoundry:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
            
            
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED FOUNDRY at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        
        # Leave the queue, do the work, and release the worker
        self.leave(foundryQueue)
        yield self.hold(timeFoundry)
        self.release((foundry, 1))
        # Wait until the endtime
        currentTime = math.floor(env.now())
        getCurrentDay()
        yield self.hold((currentDay*fullDay)-midnightWait-currentTime)
                
        
        # Update statistics
        SimulationStatistics.STAT_forged+=1
        Storage3()
        
#-Machiner-----------------------------------------------------------------------------------
class Machine(sim.Component):
    def process(self):
                 
        
        # Enter queue
        self.enter(machiningQueue)
        yield self.request((machine, 1))
        
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        
        
        print(str(currentTime))
        print(str(remaining))
        print(str(currentDay*fullDay))
        
        
        if remaining < timeMachining:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
            
            
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED MACHINING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        
        # Leave the queue, do the work, and release the worker    
        self.leave(machiningQueue)
        yield self.hold(timeMachining)
        self.release((machine, 1))
        # No need to wait!
                
        
        # Update statistics
        SimulationStatistics.STAT_machined+=1
        Print()

#-Printer-s----------------------------------------------------------------------------------
class Print(sim.Component):
    def process(self):
                
        
        # Enter queue
        self.enter(printingQueue)
        yield self.request((printer, 1))
        
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timePrinting:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            print("gonna wait->: "+str(waitingTime))
            yield self.hold(waitingTime)
            
            
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED PRINTING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
#        
        # Leave the queue, do the work, and release the worker
        self.leave(printingQueue)
        yield self.hold(timePrinting)
        self.release((printer, 1))
        # Wait until the endtime
        currentTime = math.floor(env.now())
        getCurrentDay()
        yield self.hold((currentDay*fullDay)-midnightWait)
                
        
        # Update statistics
        SimulationStatistics.STAT_printed+=1
        Storage4()

#-Brancher-----------------------------------------------------------------------------------
class BranchWheels(sim.Component):
    def process(self):
        decision = random.randint(0, 100)
        finalStorage.nWheels+=1
        if (decision < wheelAssemblyRate):
            if (finalStorage.nWheels>3 and finalStorage.nDecks>0):
                Assemble()
        else:
            if finalStorage.nWheels>=4:
                PackWheels()
            
#-PackWheels---------------------------------------------------------------------------------
class PackWheels(sim.Component):
    def process(self):
        
        
        # Semaphore checking (sim states)
        updateStates()
        yield self.wait(packWheelAllowed, fail_delay = packWheelFailWait)
        finalStorage.nWheels-=4
        SimulationStatistics.STAT_wheelToPacking+=4
         
        
        # Enter queue
        self.enter(packingWheelsQueue)
        yield self.request((wheelPacker,1))
            
        
        # Verify if there is enough time on the day to paint
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timePackingWheels:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
            
          
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED WHEEL PACKING at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
#        
        # Leave the queue, do the work, and release the worker
        self.leave(packingWheelsQueue)
        yield self.hold(timePackingWheels)
        self.release((wheelPacker,1))
                
        
        # Update statistics
        SimulationStatistics.STAT_packedWheels+=1
        finalStorage.packedWheels+=1
        
#///////////////////////////////////////////////////////////////////////////////////////////#        





def updateStates():
    if(finalStorage.nWheels>=4 and finalStorage.nDecks>=1):
        assembleAllowed.set()
    else:
        assembleAllowed.reset()
    if(finalStorage.nDecks>=8):    
        packDeckAllowed.set()
    else:
        packDeckAllowed.reset()
    if(finalStorage.nWheels>=4):
        packWheelAllowed.set()
    else:
        packWheelAllowed.reset()










 
#///////////////////////////////////////////////////////////////////////////////////////////#  
#                                       ASSEMBLE                                            #
#-Assembler class----------------------------------------------------------------------------
class Assemble(sim.Component):
    def process(self):
        
        updateStates()
        yield self.wait(assembleAllowed, fail_delay=assembleFailWait)
        
        finalStorage.nWheels-=4
        finalStorage.nDecks -=1
        SimulationStatistics.STAT_deckToAssembly+=1
        SimulationStatistics.STAT_wheelToAssembly+=4
        
        self.enter(assemblyQueue)
        yield self.request((assembler,1))
            
        # Verify if there is enough time on the day to assemble
        currentTime = env.now()
        getCurrentDay()
        remaining = currentDay*fullDay-midnightWait-currentTime
        if remaining < timeAssemblyLine:
            currentTime = env.now()
            getCurrentDay()
            waitingTime = nightWait + remaining
            yield self.hold(waitingTime)
        
        
        # Printing
#        currentTime = env.now()
#        getCurrentDay()
#        print("-----------------------------------------------------------------------------------")
#        print(str(env.now()))
#        hours=math.floor(currentTime - (currentDay-1)*fullDay)
#        minutes=math.floor((currentTime - (currentDay-1)*fullDay- hours)*60)
#        print(str(SimulationStatistics.STAT_pressed)+" -> ENTERED ASSEMBLY at: "+str(hours)+"h"+str(minutes)+"m [DAY: "+str(currentDay)+"]")
#        
        
        # Leave the queue, do the work, release the worker
        self.leave(assemblyQueue)
        yield self.hold(timeAssemblyLine)
        self.release((assembler,1))
                
        
        # Update statistics
        SimulationStatistics.STAT_packedSkates+=1
        
 #//////////////////////////////////////////////////////////////////////////////////////////#         














       
#///////////////////////////////////////////////////////////////////////////////////////////#
#                                   SIMULATION ENV                                          #
#-Simulation Environment, Queues and Resources-----------------------------------------------  
env = sim.Environment(time_unit="hours", trace=False)  

assembleAllowed     = sim.State('assembleAllowed')
packWheelAllowed    = sim.State('packWheelAllowed')
packDeckAllowed     = sim.State('packDeckAllowed')

press           = sim.Resource("press"         ,capacity = nPress)
cutter          = sim.Resource("cutter"        ,capacity = nCutter)
machine         = sim.Resource("machine"       ,capacity = nMachine)
printer         = sim.Resource("printer"       ,capacity = nPrinter*10)
painter         = sim.Resource("painter"       ,capacity = nPainter)
foundry         = sim.Resource("foundry "      ,capacity = nFoundry)
finisher        = sim.Resource("finisher"      ,capacity = nFinisher)
deckPacker      = sim.Resource("deckPacker"    ,capacity = nPackingDecks)
wheelPacker     = sim.Resource("wheelPacker"   ,capacity = nPackingWheels)
assembler       = sim.Resource("assembler"     ,capacity = nSkateAssembler)

pressQueue              = sim.Queue("pressQueue")
foundryQueue            = sim.Queue("foundryQueue")
cuttingQueue            = sim.Queue("cuttingQueue")
printingQueue           = sim.Queue("printingQueue")
paintingQueue           = sim.Queue("paintingQueue")
machiningQueue          = sim.Queue("machiningQueue")
finishingQueue          = sim.Queue("finishingQueue")
packingDecksQueue       = sim.Queue("packingDecksQueue")
packingWheelsQueue      = sim.Queue("packingWheelsQueue")
assemblyQueue           = sim.Queue("assemblyQueue")


Factory(boards=MODEL_boardLots*nBoardLots, wheels=MODEL_wheelLots*nWheelLots)
env.run(till=totalTime)

print("---------------------------------------")
print("                 BOARDS                ")
print("          >Pressed Decks: %d" % (SimulationStatistics.STAT_pressed))
print("          >Cut Decks: %d" % (SimulationStatistics.STAT_cut))
print("          >Finished Decks: %d" % (SimulationStatistics.STAT_finished))
print("          >Painted Decks: %d" % (SimulationStatistics.STAT_painted))
print("Decks that went to assembly: %d" % (SimulationStatistics.STAT_deckToAssembly))
print("Decks that went to packing: %d" % (SimulationStatistics.STAT_deckToPacking))
print("Packed Decks: %d" % (SimulationStatistics.STAT_packedDecks))
print("---------------------------------------")
print("                 WHEELS                ")
print("          >Forged Wheels: %d" % (SimulationStatistics.STAT_forged))
print("          >Machined Wheels: %d" % (SimulationStatistics.STAT_machined))
print("          >Printed Wheels: %d" % (SimulationStatistics.STAT_printed))
print("Wheels that went to assembly: %d" % (SimulationStatistics.STAT_wheelToAssembly))
print("Wheels that went to packing: %d" % (SimulationStatistics.STAT_wheelToPacking))
print("Packed Wheels: %d" % (SimulationStatistics.STAT_packedWheels))
print("---------------------------------------")
print("Packed Skates: %d" % (SimulationStatistics.STAT_packedSkates))
#///////////////////////////////////////////////////////////////////////////////////////////#