"""
Master node implementation for distributed NEAT.
"""

import socket
import threading
import time
import logging
import uuid
from typing import List, Dict, Callable

from ..population import Population
from .protocol import (
    MessageType, WorkerState, GenomePackage, BatchContainer,
    FitnessResult, WorkerStatus, send_message, receive_message,
    serialize_genome, deserialize_genome
)
from .config import DistributedConfig

class DistributedPopulation(Population):
    def __init__(self, pop_size: int, num_inputs: int, num_outputs: int,
                 config=None, distributed_config: DistributedConfig = None):
        super().__init__(pop_size, num_inputs, num_outputs, config)
        self.distributed_config = distributed_config or DistributedConfig()
        self.coordinator = SystemCoordinator(
            self.distributed_config.host,
            self.distributed_config.port,
            self.distributed_config
        )
        self.coordinator.start_server()
        self._wait_for_workers()
    
    def _wait_for_workers(self):
        print(f"Waiting for {self.distributed_config.min_workers} workers...")
        while len(self.coordinator.get_available_workers()) < self.distributed_config.min_workers:
            time.sleep(0.5)
    
    def run_generation(self, fitness_function: Callable):
        self._distributed_fitness_evaluation(fitness_function)
        for s in self.species:
            s.calculate_average_fitness()
        super().run_generation(lambda g: None)

    def _distributed_fitness_evaluation(self, fitness_function: Callable):
        genome_packages = [
            GenomePackage(g.id, serialize_genome(g), generation=self.generation)
            for g in self.genomes
        ]
        
        workers = self.coordinator.get_available_workers()
        if not workers:
            return
            
        batch_size = len(genome_packages) // len(workers)
        batches = []
        for i in range(len(workers)):
            start = i * batch_size
            end = None if i == len(workers) - 1 else (i + 1) * batch_size
            batch = BatchContainer(str(uuid.uuid4()), i, genome_packages[start:end], "fitness")
            batches.append(batch)
            
        results = self.coordinator.distribute_and_collect(batches)
        fitness_map = {r.genome_id: r.fitness_score for r in results}
        for genome in self.genomes:
            genome.fitness = fitness_map.get(genome.id, 0.0)
    
    def shutdown(self):
        self.coordinator.shutdown_workers()
        self.coordinator.stop_server()

class SystemCoordinator:
    def __init__(self, host: str, port: int, config: DistributedConfig):
        self.host = host
        self.port = port
        self.config = config
        self.workers = {}
        self.running = False
        self.lock = threading.Lock()
        
    def start_server(self):
        self.server_socket = socket.class_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        
    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._register_worker, args=(conn, addr), daemon=True).start()
            except: pass
            
    def _register_worker(self, conn, addr):
        try:
            msg_type, data = receive_message(conn)
            if msg_type == MessageType.WORKER_REGISTRATION:
                worker_id = len(self.workers)
                with self.lock:
                    self.workers[worker_id] = {'conn': conn, 'addr': addr}
                send_message(conn, MessageType.REGISTRATION_ACK, {})
        except: conn.close()
        
    def get_available_workers(self):
        with self.lock: return list(self.workers.keys())
        
    def distribute_and_collect(self, batches):
        results = []
        threads = []
        for i, batch in enumerate(batches):
            worker_id = i % len(self.workers)
            t = threading.Thread(target=self._handle_batch, args=(worker_id, batch, results))
            t.start()
            threads.append(t)
        for t in threads: t.join()
        return results
        
    def _handle_batch(self, worker_id, batch, all_results):
        try:
            conn = self.workers[worker_id]['conn']
            send_message(conn, MessageType.TASK_ASSIGNMENT, batch)
            msg_type, data = receive_message(conn)
            if msg_type == MessageType.FITNESS_REPORT:
                with self.lock: all_results.extend(data['results'])
        except: pass
        
    def shutdown_workers(self):
        with self.lock:
            for w in self.workers.values():
                try: send_message(w['conn'], MessageType.SHUTDOWN_SIGNAL, {})
                except: pass
                
    def stop_server(self):
        self.running = False
        try:
             self.server_socket.close()
        except: pass
