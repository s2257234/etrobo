from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor
import math

# インスタンスの壁を変えて管理したい変数群

class Status:
    def __init__(self):
        # タイヤの幅（定数）
        self.wheel_width = 125




        # モーターの回転数の差分
        self.right_count = 0
        self.left_count = 0

        # モーターのベース回転数
        self.base_right_count = 0
        self.base_left_count = 0

        # 移動総距離
        self.distance = 0

        # 絶対座標
        self.position_x = 0
        self.position_y = 0
        self.position_a = 0

        # 相対座標
        self.rel_x = 0
        self.rel_y = 0
        self.rel_theta = 0

        # センサー値
        self.red = 0
        self.green = 0
        self.blue = 0

        self.s = 0


        self.min_target_red = 255
        self.max_target_red = 1
        self.target_red = 0



        # 1フレーム当たりの回転数関係の差分
        self.now_right_count = 0
        self.now_left_count = 0


        # 線に対する相対的な現在位置に関する変数
        self.e_red = 0
        self.e_green = 0
        self.e_blue = 0
        self.e_s = 0

        self.prev_e_red = 0
        self.prev_e_green = 0
        self.prev_e_blue = 0
        self.prev_e_s = 0



    def reset(self, right_motor: Motor, left_motor: Motor):
        self.base_right_count = right_motor.get_count()
        self.base_left_count = left_motor.get_count()

        self.distance = 0
        self.position_x = 0
        self.position_y = 0
        self.position_a = 0



    def update(self, 
            right_motor: Motor, 
            left_motor: Motor, 
            color_sensor: ColorSensor,
        ):

        prev_right_count = self.now_right_count
        prev_left_count = self.now_left_count

        self.now_left_count = left_motor.get_count()
        self.now_right_count = right_motor.get_count()


        # 1フレーム当たりの回転数の差分
        left_count_delta = self.now_left_count - prev_left_count
        right_count_delta = self.now_right_count - prev_right_count



        self.right_count = self.now_right_count - self.base_right_count
        self.left_count = self.now_left_count - self.base_left_count



        self.red, self.green, self.blue = color_sensor.get_raw_color()
        if max(self.red, self.green, self.blue) != 0:
            self.s = (max(self.red, self.green, self.blue) - min(self.red, self.green, self.blue)) / max(self.red, self.green, self.blue)


        self.prev_e_red = self.e_red
        self.prev_e_s = self.e_s

        # 0.3 , 0.1想定
        self.e_s = 50 / (0.29) * (self.s - 0.155)

        if self.max_target_red - self.min_target_red != 0 and self.red - self.target_red != 0:
            self.e_red = 50 / (self.max_target_red - self.min_target_red) * (self.red - self.target_red)



        left_distance = abs(self.left_count)
        right_distance = abs(self.right_count)

        self.distance = (left_distance + right_distance) * 0.5


        # 自己位置推定
        # 座標の更新
        # rel　＝　1フレーム当たりの偏差
        # rel_a = 1フレーム当たりの角度の偏差
        # rel_x = 1フレーム当たりのx座標の偏差
        # rel_y = 1フレーム当たりのy座標の偏差
        # rad = 1フレーム当たりの回転半径

        if left_count_delta == right_count_delta:
            rel_a = 0.0
            rel_x = left_count_delta
            rel_y = 0.0
        else:
            rad = (
                self.wheel_width * (left_count_delta + right_count_delta) * 0.5
                / (left_count_delta - right_count_delta))
            rel_a = (left_count_delta - right_count_delta) / self.wheel_width
            rel_x = rad * math.sin(rel_a)
            rel_y = rad * (1.0 - math.cos(rel_a))

        self.position_x += rel_x * math.cos(self.position_a) - rel_y * math.sin(self.position_a)
        self.position_y += rel_x * math.sin(self.position_a) + rel_y * math.cos(self.position_a)
        self.position_a += rel_a

        while self.position_a > math.pi:
            self.position_a -= math.pi * 2.0

        while self.position_a < -math.pi:
            self.position_a += math.pi * 2.0



        #print(self.e_s, self.prev_e_s, self.s)
        #print(self.red, self.max_target_red, self.min_target_red, self.target_red)
        #print(self.e_red, self.prev_e_red)
        #print("rel_x: ", rel_x, "rel_y: ", rel_y, "rel_a: ", rel_a, "position_x: ", self.position_x, "position_y: ", self.position_y, "position_a: ", self.position_a)