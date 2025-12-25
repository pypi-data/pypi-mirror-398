JOB_DEFINITIONS = {
    "emtp": {
        "rid": "function/CloudPSS/emtp",
        "args": {
            "debug":
            "0",
            "n_cpu":
            "1",
            "solver":
            "0",
            "end_time":
            "1",
            "task_cmd":
            "",
            "step_time":
            "0.0001",
            "begin_time":
            "0",
            "task_queue":
            "",
            "initial_type":
            "0",
            "ramping_time":
            "0",
            "load_snapshot":
            "0",
            "save_snapshot":
            "0",
            "solver_option":
            "0",
            "output_channels": [{
                0: "aa",
                1: "1000",
                2: "compressed",
                3: "",
                4: [""]
            }],
            "max_initial_time":
            "1",
            "load_snapshot_name":
            "",
            "save_snapshot_name":
            "snapshot",
            "save_snapshot_time":
            "1"
        },
        "name": "电磁暂态仿真方案 1"
    },
    'sfemt': {
        "name": "移频电磁暂态仿真方案 1",
        "rid": "function/CloudPSS/sfemt",
        "args": {
            "begin_time":
            "0",
            "end_time":
            "1",
            "step_time":
            "0.0001",
            "output_channels": [{
                0: "aa",
                1: "1000",
                2: "compressed",
                3: "",
                4: [""]
            }],
            "solver":
            "0",
            "shift_freq":
            "50",
            "numerical_oscillation_suppression":
            "1",
            "ess":
            "0",
            "ess_time":
            "1e-6",
            "initial_type":
            "0",
            "ramping_time":
            "0",
            "max_initial_time":
            "1",
            "save_snapshot":
            "0",
            "save_snapshot_time":
            "1",
            "save_snapshot_name":
            "snapshot",
            "load_snapshot":
            "0",
            "load_snapshot_name":
            "",
            "task_queue":
            "",
            "solver_option":
            "0",
            "n_cpu":
            "1",
            "task_cmd":
            "",
            "debug":
            "0"
        }
    },
    "powerFlow": {
        "name": "潮流计算方案 1",
        "rid": "function/CloudPSS/power-flow",
        "args": {
            "UseBusVoltageAsInit": "1",
            "UseBusAngleAsInit": "1",
            "UseVoltageLimit": "1",
            "UseReactivePowerLimit": "1",
            "SkipPF": "0",
            "MaxIteration": "30"
        }
    },
    "iesLoadPrediction": {
        "name": "负荷预测方案 1",
        "rid": "function/CloudPSS/ies-load-prediction",
        "arcs": {
            "startTime": "2022 -01-01 00:00:00",
            "endTime": "2022 -12-31 23:00:00",
            "layer_forcast": "0",
            "forcast_algorithm": "0",
            "ratio_sub": [],
            "ratio_feeder": [],
            "ratio_trans": []
        }
    },
    "iesPowerFlow": {
        "name": "时序潮流方案 1",
        "rid": "function/CloudPSS/ies-power-flow",
        "arcs": {
            "startTime": "2022 -01-01 00:00:00",
            "endTime": "2022 -12-31 23:00:00",
            "solveMethod": "0",
            "maxIteration": "30"
        }
    },
    "iesEnergyStoragePlan": {
        "name": "储能规划方案 1",
        "rid": "function/CloudPSS/ies-energy-storage-plan",
        "arcs": {
            "Planyear": "15",
            "NetConfig": [],
            "SourceConfig": [],
            "LoadConfig": []
        }
    }

}