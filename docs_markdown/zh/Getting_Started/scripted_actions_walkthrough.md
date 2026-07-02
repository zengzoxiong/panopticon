# 脚本操作演示演练

简单演示示例是一个展示脚本化代理与 BLADE Gymnasium 环境交互的场景。在该场景中，脚本化代理指挥一架飞机打击敌机、渗透两个敌方 SAM，最后返回基地。演示代码位于 demo.py。下面我们简要解释演示代码。请确保在继续之前完成安装步骤。

## 环境设置

下面的代码片段实例化了一个 BLADE Gymnasium 环境。请注意，我们必须首先创建一个用场景 JSON 文件实例化的 Game 对象，并将其传递到环境中。场景也会被录制，录制内容可以在客户端 GUI 中回放。场景 JSON 文件可以使用 panopticon-ai Web 应用程序生成。

```python
game = Game(
    current_scenario=Scenario(),
    record_every_seconds=30,
    recording_export_path=demo_folder,
)
with open(f"{demo_folder}/simple_demo.json", "r") as scenario_file:
    game.load_scenario(scenario_file.read())

env = gymnasium.make("blade/BLADE-v0", game=game)

observation, info = env.reset()
```

## 脚本化代理

下面的代码片段定义了一个简单的脚本化代理，在特定时间步执行某些操作。

- 在时间步 0，代理从 Suelf AB 起飞一架蓝方飞机。
- 在时间步 1，代理指挥飞机飞往坐标 (10.9, -22.7)。
- 当飞机飞行到一半时，代理指挥飞机打击呼号为"Flanker #2097"的红方敌机。
- 当飞机接近第一个航路点时，代理指挥飞机飞往坐标 (15.75, -8.97) 的下一个航路点。飞机必须穿过两个 SAM 之间的狭窄走廊。
- 当飞机足够接近敌方空军基地时，代理将指挥飞机返回基地。

```python
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
    if current_time_step == 0:  # 从蓝方空军基地起飞一架飞机
        return sample_launch_aircraft_action
    elif (
        current_time_step == 1
    ):  # 在时间步 1 将起飞的飞机移至 (10.9, -22.7)
        return first_move_aircraft_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 15
        and launched_aircraft.longitude > -11
        and launched_aircraft.rtb == False
    ):  # 飞机渗透敌方空军基地后返回基地
        return return_to_base_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 10
        and launched_aircraft.longitude > -23
        and launched_aircraft.rtb == False
    ):  # 摧毁红方目标后将飞机移至 (16.05, -8.97)
        return second_move_aircraft_action
    elif (
        launched_aircraft != None
        and launched_aircraft.latitude > 0
        and launched_aircraft.longitude > -33
        and launched_aircraft.rtb == False
    ):  # 当飞机接近 (10.9, -22.7) 时攻击红方目标
        return attack_target_action  # 发射导弹
    else:
        return ""
```

## 主仿真循环

演示在特定时间步将观测输出到 JSON 文件以进行可视化。演示还以 JSONL 文件的形式输出录制内容，可以在客户端 GUI 中回放。

以下代码片段定义了主环境/仿真循环：

```python
game.start_recording()
game.record_step()
steps = 35000
for step in range(steps):
    action = simple_scripted_agent(observation)
    observation, reward, terminated, truncated, info = env.step(action=action)
    # env.unwrapped.pretty_print(observation)
    game.record_step()

env.unwrapped.export_scenario(
    f"{demo_folder}/simple_demo_t{steps}.json"
)  # 蓝方飞机应该正在返回基地
game.export_recording()
```
