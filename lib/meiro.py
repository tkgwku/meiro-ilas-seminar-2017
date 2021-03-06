# coding: utf-8

import itertools
import random
import time
import math
from PIL import Image

class AbstractMeiro(object):
    DEBUG = False
    entrance_desc = [
        'left-bottom and right-top',
        'center-bottom and center-top',
        'randomly select points at left and right side',
        'randomly select points at top and bottom side',
        'random point and the most distant point'
    ]

    def __init__(self, column, row, interval, boldness, entrancetype):
        self.column   = column   # horizontal pillars count plus 1
        self.row      = row      # vertical pillars count plus 1
        self.interval = interval # interval pixels
        self.boldness = boldness # width pixels of black line
        self.entrancetype = entrancetype #the position of two entrances

        # unoccupied pillars, (x,y)s list
        self.pillarsUnoc = []
        # pillars temporarily used in specific phase
        self.pillarsUsed = []
        # how many times loop is executed to make meiro
        self.finishcount = 0
        # how long it takes to make meiro
        self.ms = 0
        self.timerStart()

        self.white = (255,255,255)
        self.black = (60,60,60)
        self.red = (255, 175, 209)
        self.blue = (175, 212, 255)

        # parameter 1
        #self.phaseCount = int(max(column, row)/20)
        self.phaseCount = int(max(column, row)/40)

        self.phaseUnoc = [[] for i in range(0, self.phaseCount-1)]#[[],[]]
            
        for i, j in itertools.product(range(1, column), range(1, row)):
            self.pillarsUnoc.append((i,j))
            for k in range(0, self.phaseCount-1):#0,1
                if self.isIn(i, j, k+1):
                    self.phaseUnoc[k].append((i,j))
                    break

        self.phaseLen = [len(x) for x in self.phaseUnoc]
        if entrancetype == 1:
            self.start = (int(self.column/2)*2-1, self.row*2)
            self.goal = (int(self.column/2)*2-1, 0)
        elif entrancetype == 2:
            self.start = (random.randint(1, self.column)*2-1, self.row*2)
            self.goal = (random.randint(1, self.column)*2-1, 0)
        elif entrancetype == 3:
            self.start = (self.column*2, random.randint(1, self.row)*2-1)
            self.goal = (0, random.randint(1, self.row)*2-1)
        elif entrancetype == 4:
            which_edge = random.randint(1,4)
            self.goal = None
            if which_edge == 1:
                self.start = (random.randint(1, self.column)*2-1, self.row*2)
            elif which_edge == 2:
                self.start = (random.randint(1, self.column)*2-1, 0)
            elif which_edge == 3:
                self.start = (self.column*2, random.randint(1, self.row)*2-1)
            else:
                self.start = (0, random.randint(1, self.row)*2-1)
        else:
            self.start = (self.column*2-1, 0)
            self.goal = (1, self.row*2)

    def isIn(self, i, j, k):
        return min(i, self.column-i) < k*self.column/(2*self.phaseCount) or min(j, self.row-j) < k*self.row/(2*self.phaseCount)

    '''
    ()Z
    make meiro route
    '''
    def makeRoute(self):
        if self.column < 0 or self.row < 0:
            print('[error] invalid argument of column or row')
            return False

        _count = 0
        pillar = (0,0)
        prevDir = -1
        phase = 0
        maxSearchCount = 1000000
        self.walls = dict()
        for x, y in itertools.product(range(0, self.column*2+1), range(0, self.row*2+1)):
            self.walls[(x,y)] = 0
        print('[info] generating {0}*{1} maze...'.format(self.column, self.row))
        while True:
            if phase < self.phaseCount-1 and len(self.phaseUnoc[phase]) < self.phaseLen[phase]/5: # parameter 2
                phase += 1
                print('[info] phase {0}/{1}... ({2} sec)'.format(phase, self.phaseCount-1, int(time.time() * 100 - self.ms/10)/100))

            if pillar == (0,0):
                pillar = self.getUnocPillarRandomly(phase)
                self.pillarsUsed.append(pillar)
                prevDir = -1

            direction = self.makeNewDirection(prevDir)
            prevDir = direction
            pillar = self.makeNext(pillar, direction)

            if len(self.pillarsUnoc) == 0:
                self.finishcount = _count
                break

            _count += 1
            if _count > maxSearchCount:
                print('[error] detected excessive loop. generating will stop...')
                ## debug ##
                if AbstractMeiro.DEBUG:
                    for pillar in self.pillarsUnoc:
                        self.drawWall(pillar, pillar, (0, 255, 0))
                return False
        self.timerStop()
        if AbstractMeiro.DEBUG:
            print('[debug] took {} seconds'.format(self.ms/1000))
            print('[debug] took {} counts'.format(self.finishcount))
        # make edge wall
        self.drawWall((0,0), (0, self.row), self.black)
        self.drawWall((0,0), (self.column, 0), self.black)
        self.drawWall((self.column,0), (self.column, self.row), self.black)
        self.drawWall((0,self.row), (self.column, self.row), self.black)
        if self.entrancetype == 4:
            print('[info] finished making route')
            print('[info] making depth map...')
            self.timerStart()
            self.edge_depth_map = dict()
            self.edge_depth_map_loop_count = 0
            self.edgeDepthMapLoop(self.start, None, 0)
            self.timerStop()
            print('[info] depth map has been made ({0} ms, {1} loop)'.format(int(self.ms),self.edge_depth_map_loop_count))
            max_depth = max(self.edge_depth_map.values())
            for c in self.edge_depth_map:
                if self.edge_depth_map[c] == max_depth:
                    if c[0] == 1:
                        self.goal = (0,c[1])
                    if c[1] == 1:
                        self.goal = (c[0],0)
                    if c[0] == self.column*2-1:
                        self.goal = (self.column*2,c[1])
                    if c[1] == self.row*2-1:
                        self.goal = (c[0],self.row*2)
            if self.goal == None:
                print('[error] couldn\'t calculate depth properly')
                quit()
        self.fillPoint(self.start, self.red)
        self.fillPoint(self.goal, self.blue)
        return True


    def edgeDepthMapLoop(self, coord, fromCoord, depth):
        nexts = list()
        self.edge_depth_map_loop_count += 1

        if coord[0] == 1 or coord[0] == self.column*2 -1 or coord[1] == 1 or coord[1] == self.row*2-1:
            if not coord in self.edge_depth_map:
                self.edge_depth_map[coord] = depth

        for x in range(0,4):
            c = self.getNextPillar(coord, x)
            if c[0] < 0 or c[0] > self.column*2 or c[1] < 0 or c[1] > self.row*2 or c == fromCoord:
                continue
            elif self.walls[c] == 0: # space
                nexts.append(x)

        # 行き止まり
        if len(nexts) == 0:
            pass
        # 交差点
        elif len(nexts) >= 1:
            for nextdir in nexts:
                self.edgeDepthMapLoop(self.getNextPillar(coord, nextdir), coord, depth+1)
    '''
    ()V
    save meiro in some way
    @abstractmethod
    '''
    def save(self):
        pass

    '''
    (tuple2)tuple2
    process the next pillar
    '''
    def makeNext(self, currentPillar, direction):
        nextPillar = self.getNextPillar(currentPillar, direction)
        state = self.getWallMakingState(nextPillar)
        if state == State.ABORT:
            if AbstractMeiro.DEBUG:
                self.debugSave()
            self.pillarsUsed = []
            return (0,0)
        elif state == State.SAVE:
            self.pillarsUsed.append(nextPillar)
            self.saveChanges()
            return (0,0)
        elif state == State.KEEP:
            self.pillarsUsed.append(nextPillar)
            return nextPillar

    '''
    ()V
    turn temporary pillars into wall
    '''
    def saveChanges(self):
        for (i, pillar) in enumerate(self.pillarsUsed):
            if i <= len(self.pillarsUsed) -2:
                self.drawWall(pillar, self.pillarsUsed[i+1], self.black)
            if pillar in self.pillarsUnoc:
                self.rm(pillar)
        self.pillarsUsed = []

    def rm(self, pillar):
        self.pillarsUnoc.remove(pillar)
        temp = []
        for phase in self.phaseUnoc:
            if pillar in phase:
                phase.remove(pillar)
            temp.append(phase)
        self.phaseUnoc = temp
        del temp

    '''
    ()V
    turn temporary pillars into wall
    '''
    def debugSave(self):
        for (i, pillar) in enumerate(self.pillarsUsed):
            if i <= len(self.pillarsUsed) -2:
                self.drawWall(pillar, self.pillarsUsed[i+1], (255, 0, 0))

    def getUnocPillarRandomly(self, phase):
        tar = self.phaseUnoc[phase] if phase < self.phaseCount-1 else self.pillarsUnoc
        return tar[random.randint(0, len(tar)-1)]

    '''
    (tuple2, tuple2, tuple3)V
    fill canvas with certain color, from pillar to pillar
    '''
    def drawWall(self, fromPillar, toPillar, color):
        leftX  = min(fromPillar[0], toPillar[0]) * (self.boldness + self.interval)
        rightX = max(fromPillar[0], toPillar[0]) * (self.boldness + self.interval) + self.boldness # -1
        ceilY   = min(fromPillar[1], toPillar[1]) * (self.boldness + self.interval)
        bottomY = max(fromPillar[1], toPillar[1]) * (self.boldness + self.interval) + self.boldness # -1

        for x, y in itertools.product(range(leftX, rightX), range(ceilY, bottomY)):
            self.fillPoint((x,y), color)

        leftX2  = min(fromPillar[0], toPillar[0]) * 2
        rightX2 = max(fromPillar[0], toPillar[0]) * 2 + 1 # -1
        ceilY2   = min(fromPillar[1], toPillar[1]) * 2
        bottomY2 = max(fromPillar[1], toPillar[1]) * 2 + 1 # -1
        for x, y in itertools.product(range(leftX2, rightX2), range(ceilY2, bottomY2)):
            self.walls[(x,y)] = 1

    '''
    (tuple2, tuple3)V
    fill canvas with certain color at certain position
    @abstractmethod
    '''
    def fillPoint(self, pos, color):
        pass

    def makeNewDirection(self, prev):
        # 0:up 1:down 2:left 3:right
        if prev == -1:
            return random.randint(0, 3)
        else:
            _dirs = [1, 0 ,3, 2]
            del _dirs[prev]
            return _dirs[random.randint(0, 2)]

    '''
    (tuple2)tuple2
    randomly select from pillars next to current one
    '''
    def getNextPillar(self, currentPillar, direction):
        # go up
        if direction == 0:
            return (currentPillar[0], currentPillar[1]-1)
        # go down
        elif direction == 1:
            return (currentPillar[0], currentPillar[1]+1)
        # go left
        elif direction == 2:
            return (currentPillar[0]-1, currentPillar[1])
        # go right
        elif direction == 3:
            return (currentPillar[0]+1, currentPillar[1])

    '''
    (tuple2)Z
    return whether the pillar is already occupied, completed as wall
    '''
    def isOccupied(self, pillar):
        return pillar not in self.pillarsUnoc

    '''
    (tuple2)Z
    return whether the pillar is at edge wall
    '''
    def isAtEdge(self, pillar):
        return pillar[0] == 0 or pillar[1] == 0 or pillar[0] == self.column or pillar[1] == self.row

    '''
    (tuple2)State
    get the condition the pillars in
     - ABORT means they will be aborted
     - SAVE means they will survive
     - KEEP means their destiny have yet to be determined
    '''
    def getWallMakingState(self, nextPillar):
        if nextPillar in self.pillarsUsed:
            return State.ABORT
        elif self.isOccupied(nextPillar) or self.isAtEdge(nextPillar):
            return State.SAVE
        else:
            return State.KEEP

    '''
    ()V
    start timer
    '''
    def timerStart(self):
        self.ms = int(time.time() * 1000)

    '''
    ()V
    stop timer
    '''
    def timerStop(self):
        self.ms = int(time.time() * 1000) - self.ms



class State():
    ABORT = 1
    SAVE  = 2
    KEEP  = 3

'''
meiro saved as image
'''
class ImageMeiro(AbstractMeiro, object):
    def __init__(self, columns, size, fileName, entrancetype):
        super(ImageMeiro, self).__init__(columns, columns, 1, 1, entrancetype)

        self.fileName = fileName

        width = 2 * columns + 1
        self.magn = (int(size/width) + 1) * width
        self.img = Image.new('RGB', (width, width)) # canvas

        for i, j in itertools.product(range(0, width), range(0, width)):
            self.img.putpixel((i,j), self.white) # make white canvas

        print('[info] columns      : {}'.format(columns))
        print('[info] pixels       : {0}*{0}'.format(self.magn))
        print('[info] entrancetype : {0} ({1})'.format(entrancetype, AbstractMeiro.entrance_desc[entrancetype]))

    def fillPoint(self, pos, color):
        self.img.putpixel(pos, color)

    '''
    ()V
    save as RGB image file
    '''
    def save(self):
        self.img = self.img.resize((self.magn, self.magn))
        self.img.save(self.fileName)
        print('[save] saved as \'{}\''.format(self.fileName))


class SolveMeiro(object):
    linecolors = [
        (178, 41, 188),
        (178, 41, 188),
        (4, 4, 219),
        (255,0,150)
    ]
    grads = [
        [(181, 102, 255),(102, 191, 255),(42, 135, 0),(255, 255, 0),(234, 16, 74)],
        [(75,0,130),(0,0,255),(0,255,0),(255,255,0),(255,127,0),(255,0,0)],
        [(0,255,255),(255,255,255),(255,0,255)],
        [(0,0,0),(255,255,255)]
    ]
    def __init__(self, path):
        try:
            img = Image.open(path, 'r')
        except Exception as e:
            print('[error] '+e.strerror)
            quit()

        width, height = img.size

        boldness = None
        temp = None

        #bottom line
        for x in range(0, width):
            if not self.isBlack(img.getpixel((x, height-1))):
                if not temp:
                    temp = x
            else:
                if temp:
                    boldness = x - temp
                    break
        if not boldness:
            temp = None
            #left line
            for y in range(0, height):
                if not self.isBlack(img.getpixel((0,y))):
                    if not temp:
                        temp = y
                else:
                    if temp:
                        boldness = y - temp
                        break
        if not boldness:
            temp = None
            #top line
            for x in range(0, width):
                if not self.isBlack(img.getpixel((x, 0))):
                    if temp:
                        temp = x
                else:
                    if temp:
                        boldness = x - temp
                        break
        if not boldness:
            temp = None
            #right line
            for y in range(0, height):
                if not self.isBlack(img.getpixel((width-1,y))):
                    if not temp:
                        temp = y
                else:
                    if temp:
                        boldness = y - temp
                        break
        if not boldness:
            print('[error] something went wrong! There may be no entrance...?')
            quit()

        self.xlen = int(width/boldness)
        self.ylen = int(height/boldness)

        if self.xlen == 0:
            print('[error] couldn\'t resolve the boldness')
            quit()

        self.blocks = dict()

        self.start = None
        self.goal = None

        self.white = (255,255,255)
        self.black = (60,60,60)

        self.intersections = None

        #debug_string_array = ['' for i in range(0, self.ylen)]

        for i, j in itertools.product(range(0, self.xlen), range(0, self.ylen)):
            d = 0 if self.isWall((i,j), img, boldness) else 1 # 0 means that area plays role of wall
            self.blocks[(i,j)] = d
            if i == 0 or j == 0 or i == self.xlen-1 or j == self.ylen-1:
                if d == 1:
                    if self.start:
                        self.goal = (i,j)
                    elif not self.goal:
                        self.start = (i,j)
                    else:
                        print('[error] more than two entrances are detected')
                        quit()
            #debug_string_array[j] += '_' if not self.isWall((i,j)) else 'X'

        if not self.start or not self.goal:
            print('[error] no start or goal is detected')
            quit()

        #debugStr = ''
        #for line in debug_string_array:
        #    debugStr += line + '\n'

        #print(debugStr)

        print('[load] loaded   : \'{}\''.format(path))
        print('[info] size     : {0}px * {1}px'.format(width, height))
        print('[info] columns  : {0} * {1}'.format((self.ylen-1)/2, (self.xlen-1)/2))
        print('[info] entrance : {0}, {1}'.format(self.start, self.goal))

    def createSolutionMap(self, filename):
        self.intersections = list()
        self.loadintersections(self.start, None, self.start, None)
        self.save(filename)

    def isBlack(self, rgb):
        return rgb[0] < 100 and rgb[1] < 100 and rgb[2] < 100

    def isWall(self, block, img, boldness):
        sampleX = (block[0] + 0.5) * boldness
        sampleY = (block[1] + 0.5) * boldness

        sampleX = int(sampleX)
        sampleY = int(sampleY)

        return self.isBlack(img.getpixel((sampleX,sampleY)))

    def leftOf(self, coord):
        return (coord[0]-1, coord[1])

    def rightOf(self, coord):
        return (coord[0]+1, coord[1])

    def forwardOf(self, coord):
        return (coord[0], coord[1]-1)

    def backwardOf(self, coord):
        return (coord[0], coord[1]+1)

    def getcoord(self, coord, dirId):
        if dirId == 0:
            return self.forwardOf(coord)
        elif dirId == 1:
            return self.rightOf(coord)
        elif dirId == 2:
            return self.backwardOf(coord)
        else:
            return self.leftOf(coord)

    def isout(self, coord):
        return coord[0] < 0 or coord[0] >= self.ylen or coord[1] < 0 or coord[1] >= self.xlen

    def loadintersections(self, coord, fromCoord, previs, prevdir):
        nexts = list()

        for x in range(0,4):
            c = self.getcoord(coord, x)
            if self.isout(c) or c == fromCoord:
                continue
            elif self.blocks[c] == 1: # space
                nexts.append(x)

        # 通路
        if len(nexts) == 1:
            #次はgoal
            if self.getcoord(coord, nexts[0]) == self.goal:
                #最後にgoalまでのtupleを追加して終了
                tup = (self.goal, previs, prevdir)
                self.intersections.append(tup)
            #startから出たばっかり
            elif coord == self.start:
                self.loadintersections(self.getcoord(coord, nexts[0]), coord, previs, nexts[0])
            #普通の通路
            else:
                #1つ前に進む
                self.loadintersections(self.getcoord(coord, nexts[0]), coord, previs, prevdir)
        # 行き止まり
        elif len(nexts) == 0:
            #終了
            pass
        # 交差点
        elif len(nexts) > 1:
            tup = (coord, previs, prevdir)
            if previs:
                self.intersections.append(tup)
            for nextdir in nexts:
                if self.getcoord(coord, nextdir) == self.goal:
                    tup = (self.goal, coord, nextdir)
                    self.intersections.append(tup)
                else:
                    self.loadintersections(self.getcoord(coord, nextdir), coord, coord, nextdir)

    def save(self, filename):
        img2 = Image.new('RGB', (self.xlen, self.ylen))

        for x, y in itertools.product(range(0, self.xlen), range(0, self.ylen)):
            if self.blocks[(x,y)] == 1:
                img2.putpixel((x,y), self.white)
            else:
                img2.putpixel((x,y), self.black)

        #print(intersections)

        self.tploop(self.goal, img2, (255,0,150))
        #img2.putpixel(self.start, (255,0,150))

        img2 = img2.resize((self.getmgnx(), self.getmgny()))
        img2.save(filename)
        print('[save] saved solution map.')

    def drawline(self, tpl, img2, rgb):
        to = tpl[0]
        fro = tpl[1]
        dire = tpl[2]
        img2.putpixel(fro, rgb)
        c1 = self.getcoord(fro, dire)
        self.loop(c1, fro, to, img2, rgb)

    def loop(self, coord, fromCoord, to, img2, rgb):
        if coord == to:
            img2.putpixel(to, rgb)
        else:
            for x in range(0,4):
                c2 = self.getcoord(coord, x)
                if self.isout(c2) or c2 == fromCoord:
                    pass
                elif c2 == to:
                    img2.putpixel(coord, rgb)
                    img2.putpixel(to, rgb)
                elif self.blocks[c2] == 1: # space
                    img2.putpixel(coord, rgb)
                    self.loop(c2, coord, to, img2, rgb)

    def tploop(self, coord, img2, rgb):
        for tpl in self.intersections:
            if tpl[0] == coord:
                self.drawline(tpl, img2, rgb)
                self.tploop(tpl[1], img2, rgb)

    def getmgnx(self):
        return int(2000/self.xlen)*self.xlen

    def getmgny(self):
        return int(2000/self.ylen)*self.ylen

    def createDepthMap(self, depthfilename, gradationtype, drawsolution):
        print('[info] gradation type : {}'.format(gradationtype))
        print('[info] draw solution  : {}'.format(drawsolution))
        self.depthMap = dict()
        self.depthMapLoop(self.start, None, 0)
        img2 = Image.new('RGB', (self.xlen, self.ylen))
        maxdepth = max(self.depthMap.values())
        colors = SolveMeiro.grads[gradationtype]
        for x, y in itertools.product(range(0, self.xlen), range(0, self.ylen)):
            if self.blocks[(x,y)] != 1:
                img2.putpixel((x,y), self.black)
            elif (x,y) in self.depthMap:
                i = self.depthMap[(x,y)]
                img2.putpixel((x,y), self.lineargradation(i, maxdepth, colors))
            else:
                img2.putpixel((x,y), self.white)
        if drawsolution:
            if not self.intersections:
                self.intersections = list()
                self.loadintersections(self.start, None, self.start, None)
            self.tploop(self.goal, img2, SolveMeiro.linecolors[gradationtype])
            img2.putpixel(self.start, SolveMeiro.linecolors[gradationtype])
        img2 = img2.resize((self.getmgnx(), self.getmgny()))
        img2.save(depthfilename)
        print('[save] saved depth map.')

    def depthMapLoop(self, coord, fromCoord, depth):
        nexts = list()

        if not coord in self.depthMap:
            self.depthMap[coord] = depth

        for x in range(0,4):
            c = self.getcoord(coord, x)
            if self.isout(c) or c == fromCoord:
                continue
            elif self.blocks[c] == 1: # space
                nexts.append(x)

        # 行き止まり
        if len(nexts) == 0:
            pass
        # 交差点
        elif len(nexts) >= 1:
            for nextdir in nexts:
                if self.getcoord(coord, nextdir) == self.goal:
                    self.depthMap[self.goal] = depth+1
                else:
                    self.depthMapLoop(self.getcoord(coord, nextdir), coord, depth+1)

    def lineargradation(self, i, m, colors):
        l = len(colors)-1
        if i == m:
            return colors[l]
        r = i*l/m
        index = math.floor(r)
        ratio = r - index
        st = colors[index]
        fn = colors[index+1]
        r = (fn[0]-st[0])*ratio+st[0]
        g = (fn[1]-st[1])*ratio+st[1]
        b = (fn[2]-st[2])*ratio+st[2]
        return (math.floor(r),math.floor(g),math.floor(b))
