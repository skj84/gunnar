#!/usr/bin/env python
# TODO: Make this less of a hacky hot mess.
import logging
import rospy
from geometry_msgs.msg import Twist
from time import sleep
import curses
from collections import deque


WINDOWHEIGHT = 40


class KeyboardTeleop(object):
    def __init__(self, sensorDataRate=10.0):
        rospy.init_node('keyboard_teleop')
        self.publisher = rospy.Publisher('~cmd_vel', Twist, queue_size=5)
        self.sensorDataRate = sensorDataRate
        logging.basicConfig(filename='data/drive.log', level=logging.DEBUG)
        logging.debug('Begin Controller init.')
        self.stdscr = curses.initscr()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.stdscr.addstr(0, 10, 'Hit "q" to quit.')
        self.stdscr.refresh()
        self.stdscr.nodelay(True)  # Make getch non-blocking.
        
        self.twist = Twist()
        
        self.statusLines = deque()
        
        self.subscriber = rospy.Subscriber('~cmd_vel', Twist, self.printLogCallback)
        
        for s in self.textLocations:
            self.updateText(s)
        logging.debug('End Controller init.')
        
    def printLogCallback(self, data):
        self.addToLog(str(data))

    textLocations = {
        'Up': [2, 20],
        'Left': [3, 10],
        'Right': [3, 30],
        'Down': [4, 20],
        'Space': [3, 20],
        'speeds': [WINDOWHEIGHT, 0],
        'status': [WINDOWHEIGHT - 30, 1],
    }
    
    def printStatusMessage(self, *msgArgs):
        pass
#         self.gunnar.communicator.statusMessage = ' '.join(msgArgs)

    def addToLog(self, message):
        for line in message.split('\n'):
            self.addLogLine(line)

    def addLogLine(self, line, nloglines=8):
        assert '\n' not in line
        if len(self.statusLines) == nloglines:
            self.statusLines.popleft()
        self.statusLines.append(line)

    def blankLine(self, lineNo):
        self.stdscr.addstr(lineNo, 0, ' ' * 160)

    def writeRC(self, r, c, text, blank=True):
        if blank:
            self.blankLine(r)
        self.stdscr.addstr(r, c, text)
        
    def updateText(self, s):
        if s in self.textLocations:
            if s == 'status':
                firstRow, c = self.textLocations[s]
                for i, l in enumerate(self.statusLines):
                    self.writeRC(firstRow+i, c, l)
            else:
                r, c = self.textLocations[s]
                if s == 'speeds':
                    text = ''
                else:
                    text = s
                self.writeRC(r, c, text, blank=(s not in 'Right Left Space'))

    def main(self):
        key = ''
        while key != ord('q'):
            try:
                key = self.stdscr.getch()
                self.stdscr.refresh()
                if key == curses.KEY_UP:
                    self.twist.linear.x += 1
                    self.updateText('Up')
                elif key == curses.KEY_LEFT:
                    self.twist.angular.z += 1
                    self.updateText('Left')
                elif key == curses.KEY_RIGHT:
                    self.twist.angular.z -= 1
                    self.updateText('Right')
                elif key == curses.KEY_DOWN:
                    self.twist.linear.x -= 1
                    self.updateText('Down')
                elif key == ord(' '):
                    self.stop()
                    self.updateText('Space')
                sleep(1. / self.sensorDataRate)
                self.updateText('speeds');
                
                self.updateText('status');
                
                self.publisher.publish(self.twist)
                
            except KeyboardInterrupt:
                self.printStatusMessage('Press q to quit.')
        
        curses.endwin()
        
    def stop(self):
        self.twist.linear.x = 0
        self.twist.angular.z = 0


if __name__ == "__main__":
    controller = KeyboardTeleop()
    controller.main()
