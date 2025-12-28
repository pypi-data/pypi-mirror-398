import os
import time
import random
import tracemalloc
import gc
import functools

# ANSI color codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
GREY = "\033[90m" 
RESET = "\033[0m"


DEBUG = int(os.environ.get("DEBUG", 0))
N = int(os.environ.get("N",1024))

def animate(func):
    def wrapper(*args, **kwargs):
        if DEBUG == 0:
            for size, t, mem in func(*args, **kwargs):
                size_format = (
                    MAGENTA + func.__name__ +
                    GREY + "_" + YELLOW + "N" +
                    GREY + "_" + RESET + CYAN + str(size)
                )
                time_format = "        " + GREY + f"{t*1000:.4f}" + RESET + " ms"
                mem_format = "        " + GREEN + f"{mem/1024:.2f} KiB"

                print(size_format, time_format, mem_format)
                time.sleep(0.1)

        elif DEBUG == 1:
            import matplotlib.pyplot as plt
            from matplotlib.animation import FuncAnimation

            sizes = []
            times = []
            mems = []

            # Collect benchmark data
            for size, t, mem in func(*args, **kwargs):
                sizes.append(size)
                times.append(t * 1000)   # ms
                mems.append(mem / 1024)  # KiB

            if not sizes:
                print("No data to plot.")
                return

            plt.style.use("ggplot")

            fig, ax_time = plt.subplots(figsize=(8, 5))
            fig.canvas.manager.set_window_title("dsaX")

            ax_mem = ax_time.twinx()  # SECOND Y-AXIS

            ax_time.set_title(
                f"Time & Memory Performance of {func.__name__}",
                fontsize=14,
                weight="bold"
            )

            ax_time.set_xlabel("Input Size (N)", fontsize=12)
            ax_time.set_ylabel("Time (ms)", fontsize=12, color="tab:blue")
            ax_mem.set_ylabel("Memory (KiB)", fontsize=12, color="tab:red")

            ax_time.grid(False)
            ax_mem.grid(False)

            # Axis limits
            ax_time.set_xlim(0, max(sizes))
            ax_time.set_ylim(0, max(times) * 1.1)
            ax_mem.set_ylim(0, max(mems) * 1.1)

            # Lines
            line_time, = ax_time.plot(
                [], [], linewidth=2.5, label="Time (ms)", color="tab:blue"
            )
            line_mem, = ax_mem.plot(
                [], [], linewidth=2.5, linestyle="--",
                label="Memory (KiB)", color="tab:red"
            )

            # Legends
            ax_time.legend(loc="upper left")
            ax_mem.legend(loc="upper right")

            # Animation update
            def update(frame):
                line_time.set_data(sizes[:frame], times[:frame])
                line_mem.set_data(sizes[:frame], mems[:frame])
                return line_time, line_mem

            anim = FuncAnimation(
                fig,
                update,
                frames=len(sizes),
                interval=50,
                blit=False
            )

            plt.tight_layout()
            plt.show()

    return wrapper



def timeit(func, *args, **kwargs):
	st = time.perf_counter() # perf_counter() highly accurate
	func(*args, **kwargs)
	et = time.perf_counter()
	
	t = (et - st) # Seconds 
	return t


def generate(lower=None, upper=None, step = 10, sort=False):
	if lower is None:
		lower = step
	if upper is None:
		upper = N
	
	sizes = [i for i in range(lower, upper + 1, step)]
	for size in sizes:
		arr = [random.randint(1, N * N) for _ in range(size)]
		if not sort:
			yield size, arr
		else:
			yield size, sorted(arr)

def memusage(func, *args):
	gc.collect()
	tracemalloc.start()
	_ = func(*args)
	_, peak = tracemalloc.get_traced_memory()
	tracemalloc.stop()
	return peak # in Bytes
	

def benchmark(func, *args):
	t = timeit(func, *args)
	peak = memusage(func, *args)
	
	return t, peak


def memprofile(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		if not tracemalloc.is_tracing():
			tracemalloc.start()

		_ = func(*args, **kwargs)
		
		# Take a snapshot of the current memory  allocations
		snapshot = tracemalloc.take_snapshot()
		top_stats = snapshot.statistics('lineno')
		
		print(f"\n[Memory profiling for {func.__name__}]")
		# Get statistics and display the top 10 memory-consuming lines
		for stat in top_stats[:10]:
			print(stat)
		tracemalloc.stop()
		return _
	return wrapper
