# -*- coding: utf-8 -*-
"""
TCP 实时数据流演示
基于 demo.py，追加 ACMI 数据通过 TCP 发送给 Tacview
"""

import os
import gymnasium
import blade
from blade.Game import Game
from blade.Scenario import Scenario
from blade.utils.TCPStreamer import StreamConfig

demo_folder = os.path.dirname(os.path.abspath(__file__))

# 配置 TCP 流式传输
stream_config = StreamConfig(
    acmi_host="127.0.0.1",   # ACMI 目标地址
    acmi_port=42674,          # Tacview 默认端口
    send_interval=10,         # 每 10 步发送一次（降低频率）
)

game = Game(
    current_scenario=Scenario(),
    record_every_seconds=30,
    recording_export_path=demo_folder,
    enable_streaming=True,
    stream_config=stream_config,
)

with open(f"{demo_folder}/simple_demo.json", "r") as scenario_file:
    game.load_scenario(scenario_file.read())

env = gymnasium.make("blade/BLADE-v0", game=game)

# 启动 TCP 流式传输
if game.start_tcp_streaming():
    print(f"[Demo] + TCP 流式传输已启动: {stream_config.acmi_host}:{stream_config.acmi_port}")
    print("[Demo] 请在 Tacview 中连接此地址")
else:
    print("[Demo] ✗ TCP 流式传输启动失败")

observation, info = env.reset()
env.unwrapped.pretty_print(observation)


def simple_scripted_agent(observation):
    sample_launch_aircraft_action = (
        "launch_aircraft_from_airbase('05dbcb4c-dcf8-4125-ba2e-3a6fce8b33a3')"
    )
    launched_aircraft_id = "fbcaa81c-bb50-470b-9e6d-81cd825b1fd0"
    launched_aircraft_weapon_id = "1767322b-106b-418f-bd17-381590d5f916"
    first_target_position = [10.9, -22.7]
    first_move_aircraft_action = f"move_aircraft('{launched_aircraft_id}', [[{first_target_position[0]}, {first_target_position[1]}]])"
    second_target_position = [15.75, -8.97]
    second_move_aircraft_action = f"move_aircraft('{launched_aircraft_id}', [[{second_target_position[0]}, {second_target_position[1]}]])"
    red_target_id = "e0d4547d-9921-4580-bef9-5026f371cb9e"
    attack_target_action = f"handle_aircraft_attack('{launched_aircraft_id}', '{red_target_id}', '{launched_aircraft_weapon_id}', 5)"
    return_to_base_action = f"aircraft_return_to_base('{launched_aircraft_id}')"

    start_time = observation.start_time
    current_time_step = observation.current_time - start_time
    launched_aircraft = None
    aircraft = [ac for ac in observation.aircraft if ac.id == launched_aircraft_id]
    if len(aircraft) > 0:
        launched_aircraft = aircraft[0]
    if current_time_step == 0:  # launch an aircraft from the BLUE airbase
        return sample_launch_aircraft_action
    elif (
        current_time_step == 1
    ):  # move the launched aircraft to (10.9, -22.7) at timestep 1
        return first_move_aircraft_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 15
        and launched_aircraft.longitude > -11
        and launched_aircraft.rtb == False
    ):  # make the aircraft return to base after it has infiltrated the enemy airbase
        return return_to_base_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 10
        and launched_aircraft.longitude > -23
        and launched_aircraft.rtb == False
    ):  # move the launched aircraft to (16.05, -8.97) after destroying the red target:
        return second_move_aircraft_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 0
        and launched_aircraft.longitude > -33
        and launched_aircraft.rtb == False
    ):  # attack the red target when aircraft is near (10.9, -22.7)
        return attack_target_action  # launch missiles
    else:
        return ""


# 清理旧文件
for filename in os.listdir(demo_folder):
    if (
        filename.endswith(".json") and "simple_demo_t" in filename
    ) or filename.endswith(".jsonl"):
        os.remove(f"{demo_folder}/{filename}")

game.start_recording()
game.record_step()
steps = 35000
step = 0
print(f"\n[Demo] 开始仿真，共 {steps} 步...")
print("[Demo] 按 Ctrl+C 可提前停止")
print("-" * 50)

try:
    for step in range(steps):
        action = simple_scripted_agent(observation)
        observation, reward, terminated, truncated, info = env.step(action=action)
        game.record_step()

        if step % 1000 == 0:
            print(f"[Demo] 进度: {step}/{steps}")

except KeyboardInterrupt:
    print(f"\n[Demo] 用户中断，已运行 {step} 步")

finally:
    # 停止 TCP 流式传输
    game.stop_tcp_streaming()
    print("[Demo] TCP 流式传输已停止")

    # 导出录制
    env.unwrapped.export_scenario(
        f"{demo_folder}/simple_demo_t{steps}.json"
    )
    game.export_recording()
    print("[Demo] 录制已导出")
