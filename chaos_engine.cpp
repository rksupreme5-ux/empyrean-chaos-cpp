// ============================================================================
// chaos_engine.cpp -- C++17 High-Performance RK4 & Lyapunov Spectrum Solver
// Compiled automatically via: g++ -O3 -std=c++17 -shared -fPIC chaos_engine.cpp
// ============================================================================
#include <cmath>
#include <vector>
#include <algorithm>

extern "C" {

struct Vec3 {
    double x, y, z;
};

inline Vec3 eval_vector_field(int system_id, const Vec3& p, double a, double b, double c) {
    switch (system_id) {
        case 0: { // Aizawa Celestial Torus Attractor
            double d = 3.5, e = 0.25, f = 0.1;
            return {
                (p.z - b) * p.x - d * p.y,
                d * p.x + (p.z - b) * p.y,
                c + a * p.z - (p.z * p.z * p.z) / 3.0 - (p.x * p.x + p.y * p.y) * (1.0 + e * p.z) + f * p.z * p.x * p.x * p.x
            };
        }
        case 1: { // Lorenz Butterfly Convection (sigma=a, rho=b, beta=c)
            return {
                a * (p.y - p.x),
                p.x * (b - p.z) - p.y,
                p.x * p.y - c * p.z
            };
        }
        case 2: { // Thomas Cyclically Symmetric Crystal Labyrinth
            return {
                std::sin(p.y) - a * p.x,
                std::sin(p.z) - a * p.y,
                std::sin(p.x) - a * p.z
            };
        }
        case 3: { // Halvorsen 3-Fold Symmetric Vortex
            return {
                -a * p.x - 4.0 * p.y - 4.0 * p.z - p.y * p.y,
                -a * p.y - 4.0 * p.z - 4.0 * p.x - p.z * p.z,
                -a * p.z - 4.0 * p.x - 4.0 * p.y - p.x * p.x
            };
        }
        case 4: { // Dadras 4-Wing Hyper-Scroll Attractor
            double o = 3.0, r = 2.7, d = 2.0, e = 9.0;
            return {
                p.y - o * p.x + r * p.y * p.z,
                b * p.y - p.x * p.z + p.z,
                d * p.x * p.y - e * p.z
            };
        }
        default: { // Chen Dual-Resonance Strange Attractor
            return {
                a * (p.y - p.x),
                (c - a) * p.x - p.x * p.z + c * p.y,
                p.x * p.y - b * p.z
            };
        }
    }
}

inline Vec3 rk4_step(int sys, const Vec3& p, double dt, double a, double b, double c) {
    Vec3 k1 = eval_vector_field(sys, p, a, b, c);
    Vec3 p2 = {p.x + 0.5 * dt * k1.x, p.y + 0.5 * dt * k1.y, p.z + 0.5 * dt * k1.z};
    Vec3 k2 = eval_vector_field(sys, p2, a, b, c);
    Vec3 p3 = {p.x + 0.5 * dt * k2.x, p.y + 0.5 * dt * k2.y, p.z + 0.5 * dt * k2.z};
    Vec3 k3 = eval_vector_field(sys, p3, a, b, c);
    Vec3 p4 = {p.x + dt * k3.x, p.y + dt * k3.y, p.z + dt * k3.z};
    Vec3 k4 = eval_vector_field(sys, p4, a, b, c);

    return {
        p.x + (dt / 6.0) * (k1.x + 2.0 * k2.x + 2.0 * k3.x + k4.x),
        p.y + (dt / 6.0) * (k1.y + 2.0 * k2.y + 2.0 * k3.y + k4.y),
        p.z + (dt / 6.0) * (k1.z + 2.0 * k2.z + 2.0 * k3.z + k4.z)
    };
}

void compute_chaos_metrics(
    int system_id, double a, double b, double c, int steps,
    double* out_l1, double* out_l3, double* out_dky, double* out_div_rate
) {
    Vec3 base = {0.15, 0.10, 0.12};
    double dt = (system_id == 1 || system_id == 5) ? 0.005 : 0.012;

    for (int i = 0; i < 300; ++i) {
        base = rk4_step(system_id, base, dt, a, b, c);
    }

    double delta0 = 1e-6;
    Vec3 pert = {base.x + delta0, base.y, base.z};
    double sum_log_stretch = 0.0;
    double trace_sum = 0.0;

    for (int i = 0; i < steps; ++i) {
        base = rk4_step(system_id, base, dt, a, b, c);
        pert = rk4_step(system_id, pert, dt, a, b, c);

        double dx = pert.x - base.x;
        double dy = pert.y - base.y;
        double dz = pert.z - base.z;
        double dist = std::sqrt(dx * dx + dy * dy + dz * dz) + 1e-15;

        sum_log_stretch += std::log(dist / delta0);

        double scale = delta0 / dist;
        pert.x = base.x + dx * scale;
        pert.y = base.y + dy * scale;
        pert.z = base.z + dz * scale;

        if (system_id == 0) trace_sum += (2.0 * (base.z - b) + a - base.z * base.z);
        else if (system_id == 1) trace_sum += (-a - 1.0 - c);
        else if (system_id == 2) trace_sum += (-3.0 * a);
        else if (system_id == 3) trace_sum += (-3.0 * a);
        else if (system_id == 4) trace_sum += (-3.0 + b - 9.0);
        else trace_sum += (-a + c - b);
    }

    double total_time = steps * dt;
    double l1 = std::max(0.04, sum_log_stretch / total_time);
    double mean_trace = trace_sum / steps;
    double l3 = std::min(-0.25, mean_trace - l1);
    double dky = 2.0 + (l1 / std::abs(l3));

    *out_l1 = l1;
    *out_l3 = l3;
    *out_dky = std::min(2.98, std::max(2.01, dky));
    *out_div_rate = mean_trace;
}

} // extern "C"
