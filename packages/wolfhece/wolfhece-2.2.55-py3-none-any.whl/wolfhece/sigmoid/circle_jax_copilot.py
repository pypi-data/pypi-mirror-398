import jax
import jax.numpy as jnp
from jax import jit, vmap
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize, root_scalar

# Forcer float32
jax.config.update("jax_enable_x64", False)

# Fonction pour calculer l'aire immergée
def wet_area(h, R):
    h = jnp.clip(h, 0, 2 * R)
    theta = 2 * jnp.arccos(1 - h / R)
    area = (R**2 / 2) * (theta - jnp.sin(theta))
    return area

# Solution numérique "classique" pour h
def analytical_h(R, f):
    def solve_theta(theta):
        return (theta - jnp.sin(theta)) / (2 * jnp.pi) - f
    theta_min, theta_max = jnp.float32(0.0), jnp.float32(2 * jnp.pi)
    for _ in range(50):
        theta_mid = (theta_min + theta_max) / 2
        val = solve_theta(theta_mid)
        theta_max = jnp.where(val > 0, theta_mid, theta_max)
        theta_min = jnp.where(val <= 0, theta_mid, theta_min)
    theta = (theta_min + theta_max) / 2
    return R * (1 - jnp.cos(theta / 2))

# # Fonction objectif avec pondération quadratique
# def objective(h, R, f):
#     total_area = jnp.pi * R**2
#     target_area = f * total_area
#     diff = wet_area(h, R) - target_area
#     scale_factor = jnp.minimum(f, 1. - f)
#     scale = 0.1 * R**2 * (scale_factor**2 + 0.01)  # Échelle quadratique
#     return 1 / (1 + jnp.exp(-diff / scale))

# def objective(h, R, f):
#     total_area = jnp.pi * R**2
#     target_area = f * total_area
#     diff = wet_area(h, R) - target_area
#     scale_factor = jnp.minimum(f, 1. - f)
#     scale = 0.1 * R**2 * jnp.maximum(scale_factor, 0.01)
#     return 0.5 * (1 + jnp.tanh(diff / scale))


# Fonction objectif avec lissage (inchangée)
def objective(h, R, f):
    total_area = jnp.pi * R**2
    target_area = f * total_area
    diff = wet_area(h, R) - target_area
    scale_factor = jnp.minimum(f, 1. - f)
    scale = 0.05 * R**2 * jnp.maximum(scale_factor, 0.01)
    return 1 / (1 + jnp.exp(-diff / scale))

# Dichotomie douce avec préservation de la racine
@jit
def soft_dichotomy(R, f, max_iter=10000):
    f_sym = jnp.minimum(f, 1 - f)

    def body(state, _):
        h_min, h_max = state
        h_mid = (h_min + h_max) / 2
        sigmoid_val = objective(h_mid, R, f_sym)

        # Différences pour h_min, h_mid et h_max
        diff_min = wet_area(h_min, R) - f_sym * jnp.pi * R**2
        diff_max = wet_area(h_max, R) - f_sym * jnp.pi * R**2

        # Facteurs de préservation lisses
        preserve_min = jnp.exp(-jnp.abs(diff_min) / (0.01))  # Proche de 1 si h_min est racine
        preserve_max = jnp.exp(-jnp.abs(diff_max) / (0.01))  # Proche de 1 si h_max est racine

        # Mise à jour des bornes avec préservation
        h_min_new = h_min + (1. - preserve_min) * (h_mid - h_min) * (1. - sigmoid_val)
        h_max_new = h_max - (1. - preserve_max) * (h_max - h_mid) * sigmoid_val

        # # Garantie que h_min_new < h_max_new
        # h_min_new = jnp.minimum(h_min_new, h_mid - 0.01 * R)
        # h_max_new = jnp.maximum(h_max_new, h_mid + 0.01 * R)

        return (h_min_new, h_max_new), None

    h_min_init = jnp.float32(0.0)
    h_max_init = jnp.float32(2 * R)
    initial_state = (h_min_init, h_max_init)
    final_state, _ = jax.lax.scan(body, initial_state, None, length=max_iter)
    h_min, h_max = final_state
    h_sym = (h_min + h_max) / 2
    return jnp.where(f <= 0.5, h_sym, 2 * R - h_sym)

# Dérivée par rapport à f
grad_bisection = jax.grad(soft_dichotomy, argnums=1)

# Fonction objectif avec lissage
def section(h, R, f):
    total_area = jnp.pi * R**2
    target_area = f * total_area
    return wet_area(jnp.clip(h, 0, 2 * R), R) - target_area

grad_section = jax.grad(section, argnums=0)

# recherche de la recine de la section
def find_root(R, f):
    def fun(h):
        return section(h, R, f)
    def grad(h):
        return grad_section(h, R, f)

    h_root = root_scalar(fun, fprime=grad, x0=R)
    return h_root.root

h = find_root(1.,0.5)
pass

if __name__ == "__main__":
    R = jnp.float32(1.0)
    f_values = jnp.linspace(jnp.float32(0.00), jnp.float32(1.), 5000, endpoint=True)

    h_numerical = vmap(lambda f: soft_dichotomy(R, f))(f_values)
    h_analytical = vmap(lambda f: analytical_h(R, f))(f_values)
    errors = jnp.abs(h_numerical - h_analytical)

    grads = vmap(lambda f: grad_bisection(R, f))(f_values)

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 3, 1)
    plt.plot(f_values, h_numerical, label="Numérique (symétrie centrale)", color="blue")
    plt.plot(f_values, h_analytical, "--", label="Analytique", color="orange")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Hauteur (h)")
    plt.title("Hauteur en fonction de f (float32)")
    plt.legend()
    plt.grid(True)
    # plt.yscale("log")

    plt.subplot(1, 3, 2)
    plt.plot(f_values, errors, color="red")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Erreur absolue (|h_num - h_ana|)")
    plt.title("Erreur par rapport à la solution analytique")
    plt.grid(True)
    plt.yscale("log")

    plt.subplot(1, 3, 3)
    plt.plot(f_values, grads, label="Dérivée par rapport à f")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Gradient de f par rapport à h")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    for f_test in [0., 0.001, 0.01, 0.5, 0.99, 0.999]:
        f_test = jnp.float32(f_test)
        h_num = soft_dichotomy(R, f_test)
        h_ana = analytical_h(R, f_test)
        grad_h = grad_bisection(R, f_test)
        print(f"f = {f_test:.4f}:")
        print(f"  h numérique = {h_num:.6f}")
        print(f"  h analytique = {h_ana:.6f}")
        print(f"  Gradient de h par rapport à f = {grad_h:.6f}")
        print(f"  Erreur = {jnp.abs(h_num - h_ana):.6f}")
        print(f"  Erreur relative = {jnp.abs(h_num - h_ana) / h_ana:.6e}")
    pass