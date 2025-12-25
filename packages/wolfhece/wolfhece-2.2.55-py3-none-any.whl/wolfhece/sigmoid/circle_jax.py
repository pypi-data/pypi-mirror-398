import jax
import jax.numpy as jnp
from jax import jit, vmap
import matplotlib.pyplot as plt
import numpy as np
 
# Forcer float32
jax.config.update("jax_enable_x64", False)
 
# Fonction pour calculer l'aire immergée
def wet_area(h, R):
    h = jnp.clip(h, 0, 2 * R)
    theta = 2 * jnp.arccos(1 - h / R)
    area = (R**2 / 2) * (theta - jnp.sin(theta))
    return area
 
# Solution "analytique/numérique" classique pour h
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
 
# Fonction objectif avec sigmoïde adaptative aux deux bornes
def objective(h, R, f):
    total_area = jnp.pi * R**2
    target_area = f * total_area
    diff = wet_area(h, R) - target_area
    # Échelle adaptative : plus kleine pour f près de 0 ou 1
    scale_factor = jnp.minimum(f, 1. - f)  # Distance au bord le plus proche
    scale = 0.05 * R**2 * jnp.maximum(scale_factor, 0.01)  # Éviter 0
    return 1 / (1 + jnp.exp(-diff / scale))
 
# Dichotomie douce améliorée
@jit
def soft_dichotomy(R, f, max_iter=200):
    def body(state, _):
        h_min, h_max = state
        h_mid = (h_min + h_max) / 2
        sigmoid_val = objective(h_mid, R, f)
        h_min_new = h_min + (h_mid - h_min) * (1 - sigmoid_val)
        h_max_new = h_max - (h_max - h_mid) * sigmoid_val
        return (h_min_new, h_max_new), None
 
    # Bornes initiales resserrées pour petits/grands f
    h_min_init = jnp.float32(0.0)
    h_max_init = jnp.float32(2 * R)
    initial_state = (h_min_init, h_max_init)
    final_state, _ = jax.lax.scan(body, initial_state, None, length=max_iter)
    h_min, h_max = final_state
    return (h_min + h_max) / 2

# Dérivée par rapport à f
grad_bisection = jax.grad(soft_dichotomy, argnums=1)
 
  
if __name__ == "__main__":
    # Paramètres
    R = jnp.float32(1.0)
    f_values = jnp.linspace(jnp.float32(0.001), jnp.float32(0.999), 500)  # Plus près des bords
    
    # Calculs
    h_numerical = vmap(lambda f: soft_dichotomy(R, f))(f_values)
    h_analytical = vmap(lambda f: analytical_h(R, f))(f_values)
    errors = jnp.abs(h_numerical - h_analytical)

    grads = vmap(lambda f: grad_bisection(R, f))(f_values)

    # Graphiques
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 3, 1)
    plt.plot(f_values, h_numerical, label="Numérique (sigmoïde)", color="blue")
    plt.plot(f_values, h_analytical, "--", label="Analytique", color="orange")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Hauteur (h)")
    plt.title("Hauteur en fonction de f (float32)")
    plt.legend()
    plt.grid(True)
    plt.yscale("log")  # Échelle log pour voir les extrêmes
    
    plt.subplot(1, 3, 2)
    plt.plot(f_values, errors, color="red")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Erreur absolue (|h_num - h_ana|)")
    plt.title("Erreur par rapport à la solution analytique")
    plt.grid(True)
    plt.yscale("log")  # Échelle log pour les erreurs

    plt.subplot(1, 3, 3)
    plt.plot(f_values, grads, label="Dérivée par rapport à f")
    plt.xlabel("Fraction immergée (f)")
    plt.ylabel("Gradient de f par rapport à h")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()
    
    # Tests spécifiques aux deux bornes
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