from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor
import argparse

from scene5 import CalibrationScene, LineTraceScene, DoubleLoopScene, SmartCarryScene, Pattern_deburi #TestScene
from status import Status
#デブリのパターンを変える際には、from sceneの部分の数字を変える


# test中のためtest_flagをTrueにする
class Runner(object):
    def __init__(self, power: int, state:int, flag:bool) -> None:
        self.power = power
        self.state = state
        self.running = flag
        self.first_time_flag = False

        self.status = Status()

        self.calibration = CalibrationScene(0, self.status)
        self.scene_list = [
            #TestScene(power, 0, self.status),
            LineTraceScene(power, 0, self.status),
            DoubleLoopScene(power, 0, self.status),
            Pattern_deburi(power,0, self.status),
            SmartCarryScene(power, 0, self.status)
            ]
        
        self.test = SmartCarryScene(power, 0, self.status)
        self.test_flag = False

    def __call__(self, hub: Hub, right_motor: Motor, left_motor: Motor, touch_sensor: TouchSensor, color_sensor: ColorSensor) -> None:
        self.status.update(right_motor, left_motor, color_sensor)
        if self.test_flag != True:
            if self.running and self.first_time_flag:
                target, min_target, max_target = 46, 10, 80
                for state in self.scene_list:
                    state.give_any_value(target, min_target, max_target)
                self.first_time_flag = False
            else:
                self.calibration.executer(right_motor, left_motor, color_sensor)
                if self.calibration.check_finish() and (
                        touch_sensor.is_pressed()
                        or hub.is_left_button_pressed()
                        or hub.is_right_button_pressed()):
                    self.status.reset(right_motor, left_motor)
                    self.running = True
                
            if self.running:
                if self.scene_list[self.state].check_finish():
                    self.status.reset(right_motor, left_motor)
                    self.state += 1
                else:
                    self.scene_list[self.state].executer(right_motor, left_motor, color_sensor)
        else:
            if self.test.check_finish():
                self.status.reset(right_motor, left_motor)
                raise Exception("Finish")
            else:
                self.test.executer(right_motor, left_motor, color_sensor)
"""
        else:
            self.calibration.executer(right_motor, left_motor, color_sensor)
            if self.calibration.check_finish() and (
                        touch_sensor.is_pressed()
                        or hub.is_left_button_pressed()
                        or hub.is_right_button_pressed()):
                self.status.reset(right_motor, left_motor)
                self.running = True
                
            if self.running:
                if self.scene_list[self.state].check_finish():
                    self.status.reset(right_motor, left_motor)
                    self.state += 1
                else:
                    self.scene_list[self.state].executer(right_motor, left_motor, color_sensor)
           """ 




def run(backend: str, power: int, state:int, flag:bool, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(Runner(power, state, flag))
     .dispatch(**kwargs))




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='raspyke', power=90, state = 0, interval = 0.015, flag = False, logfile=args.logfile)