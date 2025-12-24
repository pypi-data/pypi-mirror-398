from pathlib import Path

def kernelMain(code):
    return f'''extern "C" void kernel_main() {{
{code}
}}
'''

def startKernel(code):
    return f'''void start_kernel() {{
{code}
}}
'''

def initSched(code):
    return f'''void init_sched() {{
{code}
}}
'''

def initMm(code):
    return f'''void init_mm() {{
{code}
}}
'''

def setupArch(code):
    return f'''void setup_arch() {{
{code}
}}
'''

def kmalloc(code):
    return f'''void* kmalloc(size_t size, int flags) {{
{code}
}}
'''

def kfree(code):
    return f'''void kfree(const void* ptr) {{
{code}
}}
'''

def vmalloc(code):
    return f'''void* vmalloc(unsigned long size) {{
{code}
}}
'''

def vfree(code):
    return f'''void vfree(const void* addr) {{
{code}
}}
'''

def copyToUser(code):
    return f'''int copy_to_user(void* to, const void* from, unsigned long n) {{
{code}
}}
'''

def copyFromUser(code):
    return f'''int copy_from_user(void* to, const void* from, unsigned long n) {{
{code}
}}
'''

def fork(code):
    return f'''struct task_struct* fork() {{
{code}
}}
'''

def schedule(code):
    return f'''void schedule() {{
{code}
}}
'''

def wakeUp(code):
    return f'''void wake_up(void* queue) {{
{code}
}}
'''

def sleepOn(code):
    return f'''void sleep_on(void* queue) {{
{code}
}}
'''

def requestIrq(code):
    return f'''int request_irq(unsigned int irq, void* handler, unsigned long flags, const char* name, void* dev) {{
{code}
}}
'''

def freeIrq(code):
    return f'''void free_irq(unsigned int irq, void* dev) {{
{code}
}}
'''

def irqHandler(code):
    return f'''int irq_handler(int irq, void* dev_id) {{
{code}
}}
'''

def readDevice(code):
    return f'''ssize_t read(void* filp, char* buf, size_t count, void* f_pos) {{
{code}
}}
'''

def writeDevice(code):
    return f'''ssize_t write(void* filp, const char* buf, size_t count, void* f_pos) {{
{code}
}}
'''

def openDevice(code):
    return f'''int open(void* inode, void* filp) {{
{code}
}}
'''

def releaseDevice(code):
    return f'''int release(void* inode, void* filp) {{
{code}
}}
'''

def spinLock(code):
    return f'''void spin_lock(void* lock) {{
{code}
}}
'''

def spinUnlock(code):
    return f'''void spin_unlock(void* lock) {{
{code}
}}
'''

def semaInit(code):
    return f'''void sema_init(void* sem, int val) {{
{code}
}}
'''

def down(code):
    return f'''void down(void* sem) {{
{code}
}}
'''

def up(code):
    return f'''void up(void* sem) {{
{code}
}}
'''

def printk(code):
    return f'''void printk(const char* fmt, ...) {{
{code}
}}
'''

def panic(code):
    return f'''void panic(const char* message) {{
{code}
}}
'''

def idleLoop(code):
    return f'''void idle_loop() {{
    while(1) {{
{code}
    }}
}}
'''

def saveAll(functions):
    for name, func_code in functions.items():
        filename = f"{name}.cpp"
        Path(filename).write_text(func_code)
        print(f"Saved {filename}.")
