if __name__ == "__main__":
    from ncuhep.muography.classes import PlaneDetector
    from ncuhep.muography.mc_renderer import MonteCarloRenderer

    # Load detector geometry
    det = PlaneDetector()
    det._import("detector_config.json")

    # Construct Monte Carlo renderer:
    #   - use GPU backend
    #   - use up to 2 GPUs (if available)
    mc = MonteCarloRenderer(
        det,
        zenith_boresight_deg=0.0,
        azimuth_boresight_deg=0.0,
        theta_max_deg=30.0,
        angle_deg_basis=25.0,
        use_gpu=True,
        max_gpus=2,             # <-- max number of GPUs to use
        state_path="9449.npz",
        log_path="9449.txt",
    )

    # Option 1: specify number of events directly
    mc.run(
        n_events=1_000_000,
        runs=1,
        iters_per_run=10,
    )

# Option 2 (commented): compute n_events from flux and live time
# mc.run(
#     flux=1.0,                        # cm^-2 s^-1 sr^-1
#     time_elapsed=36500 * 24 * 3600,  # s
#     runs=1,
#     iters_per_run=10,
# )

# If you want to change GPU usage later:
# mc.set_use_gpu(True, max_gpus=4)
# mc.run(n_events=2_000_000, runs=1, iters_per_run=5)
