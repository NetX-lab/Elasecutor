#resource monitor
import argparse
import os
import sched
import sys
import time
import psutil


class resMonitor:
    #using resprofile as the profile file
    def __init__(self, outfile_name=None, flush=False):
        print('Resource monitor started.', file=sys.stderr)
        ncores = self.ncores = psutil.cpu_count()
        if outfile_name is None:
            self.outfile = sys.stdout
        else:
            self.outfile = open(outfile_name, 'w')
        self.flush = flush
        self.outfile.write(
            'Timestamp,  Uptime, NCPU, %CPU, ' + ', '.join(['%CPU' + str(i) for i in range(ncores)]) +
            ', %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB' +
            ', %SWAP, swap.total.KB, swap.used.KB, swap.free.KB' +
            ', io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms\n')
        self.prev_disk_stat = psutil.disk_io_counters()
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        if self.outfile is not sys.stdout:
            self.outfile.close()
        self.closed = True
        print('Resource monitor closed.', file=sys.stderr)

    def poll_stat(self):
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        total_cpu_percent = psutil.cpu_percent(percpu=False)
        percpu_percent = psutil.cpu_percent(percpu=True)
        mem_stat = psutil.virtual_memory()
        swap_stat = psutil.swap_memory()
        disk_stat = psutil.disk_io_counters()

        line = str(timestamp) + ', ' + str(uptime) + ', ' + \
            str(self.ncores) + ', ' + str(total_cpu_percent*self.ncores) + ', '
        line += ', '.join([str(i) for i in percpu_percent])
        line += ', ' + str(mem_stat.percent) + ', ' + str(mem_stat.total >> 10) + ', ' + str(
            mem_stat.used >> 10) + ', ' + str(mem_stat.available >> 10) + ', ' + str(mem_stat.free >> 10)
        line += ', ' + str(swap_stat.percent) + ', ' + str(swap_stat.total >> 10) + \
            ', ' + str(swap_stat.used >> 10) + ', ' + str(swap_stat.free >> 10)
        line += ', ' + str(disk_stat.read_count - self.prev_disk_stat.read_count) + ', ' + str(disk_stat.write_count - self.prev_disk_stat.write_count) + \
                ', ' + str((disk_stat.read_bytes - self.prev_disk_stat.read_bytes) >> 10) + ', ' + str((disk_stat.write_bytes - self.prev_disk_stat.write_bytes) >> 10) + \
                ', ' + str(disk_stat.read_time - self.prev_disk_stat.read_time) + \
            ', ' + str(disk_stat.write_time - self.prev_disk_stat.write_time)

        self.outfile.write(line + '\n')
        if self.flush:
            self.outfile.flush()
        self.prev_disk_stat = disk_stat


class NetworkInterfaceMonitor:

    def __init__(self, outfile_pattern='netstat.{nic}.csv', nics=[], flush=False):
        print('NIC monitor started.', file=sys.stderr)
        all_nics = psutil.net_if_stats()
        self.nic_files = dict()
        self.flush = flush
        for nic_name in nics:
            nic_name = nic_name.strip()
            if nic_name not in all_nics:
                print('Error: NIC "%s" does not exist. Skip.' %
                      nic_name, file=sys.stderr)
            else:
                self.nic_files[nic_name] = self.create_new_logfile(
                    outfile_pattern, nic_name)
        if len(self.nic_files) == 0:
            raise ValueError('No NIC to monitor.')
        self.prev_stat = dict()
        for nic, stat in psutil.net_io_counters(pernic=True).items():
            if nic in self.nic_files:
                self.prev_stat[nic] = stat
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        for f in self.nic_files.values():
            f.close()
        self.closed = True
        print('NIC monitor closed.', file=sys.stderr)

    def create_new_logfile(self, pattern, nic_name):
        f = open(pattern.format(nic=nic_name), 'w')
        f.write(
            'Timestamp,  Uptime, NIC, sent.B, recv.B, sent.pkts, recv.pkts, err.in, err.out, drop.in, drop.out\n')
        return f

    def poll_stat(self):
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        net_stat = psutil.net_io_counters(pernic=True)
        for nic, f in self.nic_files.items():
            stat = net_stat[nic]
            prevstat = self.prev_stat[nic]
            f.write(str(timestamp) + ', ' + str(uptime) + ', ' + nic + ', ' +
                    str(stat.bytes_sent-prevstat.bytes_sent) + ', ' + str(stat.bytes_recv-prevstat.bytes_recv) + ', ' +
                    str(stat.packets_sent-prevstat.packets_sent) + ', ' + str(stat.packets_recv-prevstat.packets_recv) + ', ' +
                    str(stat.errin-prevstat.errin) + ', ' + str(stat.errout-prevstat.errout) + ', ' + str(stat.dropin-prevstat.dropin) + ', ' + str(stat.dropout-prevstat.dropout) + '\n')
            if self.flush:
                f.flush()
        self.prev_stat = net_stat

#define the resource monitored
class ProcessSetMonitor:

    BASE_STAT = {
        'io.read': 0,
        'io.write': 0,
        'io.read.KB': 0,
        'io.write.KB': 0,
        'mem.rss.KB': 0,
        '%MEM': 0,
        '%CPU': 0,
    }

    KEYS = sorted(BASE_STAT.keys())

    def __init__(self, keywords, pids, outfile_name, flush=False):
        print('ProcessSet monitor started.', file=sys.stderr)
        if outfile_name is None:
            self.outfile = sys.stdout
        else:
            self.outfile = open(outfile_name, 'w')
        self.pids = pids
        self.keywords = keywords
        self.flush = flush
        self.outfile.write('Timestamp, Uptime, ' + ', '.join(self.KEYS) + '\n')
        self.starttime = int(time.time())
        self.poll_stat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, 'closed'):
            self.close()

    def close(self):
        if self.outfile is not sys.stdout:
            self.outfile.close()
        self.closed = True
        print('ProcessSet monitor closed.', file=sys.stderr)

    def _stat_proc(self, proc, stat, visited):
        if proc.pid in visited:
            return
        visited.add(proc.pid)
        io = proc.io_counters()
        mem_rss = proc.memory_info().rss
        mem_percent = proc.memory_percent('rss')
        nctxsw = proc.num_ctx_switches()
        nctxsw = nctxsw.voluntary + nctxsw.involuntary
        nthreads = proc.num_threads()
        cpu_percent = proc.cpu_percent()
        stat['io.read'] += io.read_count
        stat['io.write'] += io.write_count
        stat['io.read.KB'] += io.read_bytes
        stat['io.write.KB'] += io.write_bytes
        stat['mem.rss.KB'] += mem_rss
        stat['%MEM'] += mem_percent
        stat['nctxsw'] += nctxsw
        stat['%CPU'] += cpu_percent
        for c in proc.children():
            self._stat_proc(c, stat, visited)

    def poll_stat(self):
        visited = set()
        curr_stat = dict(self.BASE_STAT)
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
            except psutil.NoSuchProcess:
                pass
            else:
                if pinfo['pid'] not in visited:
                    if pinfo['pid'] in self.pids:
                        self._stat_proc(proc, curr_stat, visited)
                    else:
                        for k in self.keywords:
                            if k in pinfo['name'].lower():
                                self._stat_proc(proc, curr_stat, visited)
                                break  # for keyword
        curr_stat['%CPU'] = round(curr_stat['%CPU'], 3)
        curr_stat['%MEM'] = round(curr_stat['%MEM'], 3)
        curr_stat['io.read.KB'] >>= 10
        curr_stat['io.write.KB'] >>= 10
        curr_stat['mem.rss.KB'] >>= 10
        line = str(timestamp) + ', ' + str(uptime) + ', ' + \
            ', '.join([str(curr_stat[k]) for k in self.KEYS]) + '\n'
        self.outfile.write(line)
        if self.flush:
            self.outfile.flush()


#def chprio(prio):
#    try:
#        psutil.Process(os.getpid()).nice(prio)
#    except:
#        print('Warning: failed to elevate priority!', file=sys.stderr)


#def sigterm(signum, frame):
#    raise KeyboardInterrupt()


def main():
    parser = argparse.ArgumentParser(
    #transfer the pids got here
    parser.add_argument('--ps-pids', type=int, nargs='*',
                        help='Include the specified PIDs and their children.')
    parser.add_argument('--ps-outfile', type=str, nargs='?', default='resprofile.csv')
    args = parser.parse_args()
    #monitor the dedicated pid
    if args.ps_pids is None:
        args.ps_pids = set()
    else:
        args.ps_pids = set(args.ps_pids)

    try:
        chprio(-20)
        scheduler = sched.scheduler(time.time, time.sleep)
        sm = resMonitor(args.outfile, args.flush)

        enable_nic_mon = args.nic is not None
 
        if args.enable_ps:
            pm = ProcessSetMonitor(
                args.ps_keywords, args.ps_pids, args.ps_outfile, args.flush)

        i = 1
        starttime = time.time()
        while True:
            scheduler.enterabs(
                time=starttime + i*args.delay, priority=2, action=resMonitor.poll_stat, argument=(sm, ))
            if enable_nic_mon:
                scheduler.enterabs(time=starttime + i*args.delay, priority=1,
                                   action=NetworkInterfaceMonitor.poll_stat, argument=(nm, ))
            if args.enable_ps:
                scheduler.enterabs(
                    time=starttime + i*args.delay, priority=0, action=ProcessSetMonitor.poll_stat, argument=(pm, ))
            scheduler.run()
            i += 1
        sys.exit(0)


if __name__ == '__main__':
    main()
