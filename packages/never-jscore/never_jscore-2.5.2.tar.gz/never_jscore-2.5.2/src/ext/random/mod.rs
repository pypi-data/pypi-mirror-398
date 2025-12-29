// Random extension for seedable random number generation
// Provides op_crypto_random for overriding Math.random()

use deno_core::{extension, Extension, OpState};
use rand::{Rng, SeedableRng};
use std::cell::RefCell;
use std::rc::Rc;

/// RNG state that can be seeded
pub struct RngState {
    /// Current seed (if set)
    pub seed: Option<u64>,
    /// Seeded RNG instance
    pub seeded_rng: Option<rand::rngs::StdRng>,
}

impl Default for RngState {
    fn default() -> Self {
        Self {
            seed: None,
            seeded_rng: None,
        }
    }
}

impl RngState {
    pub fn new(seed: Option<u64>) -> Self {
        if let Some(s) = seed {
            Self {
                seed: Some(s),
                seeded_rng: Some(rand::rngs::StdRng::seed_from_u64(s)),
            }
        } else {
            Self::default()
        }
    }
}

#[deno_core::op2(fast)]
/// Generate a random number (0.0 to 1.0) using seeded RNG if available
/// This is used to override Math.random() via JavaScript
pub fn op_crypto_random(state: &mut OpState) -> f64 {
    if let Some(rng_state) = state.try_borrow_mut::<Rc<RefCell<RngState>>>() {
        let mut rng = rng_state.borrow_mut();
        if let Some(ref mut seeded_rng) = rng.seeded_rng {
            // Use seeded RNG for deterministic randomness
            return seeded_rng.gen::<f64>();
        }
    }

    // Fallback to thread_rng if no seed set
    rand::thread_rng().gen::<f64>()
}

// Random extension definition using deno_core::extension! macro
extension!(
    never_jscore_random,
    ops = [op_crypto_random],
    options = {
        seed: Option<u64>,
    },
    state = |state, options| {
        let rng_state = Rc::new(RefCell::new(RngState::new(options.seed)));
        state.put(rng_state);
    }
);

/// Build random extension from ExtensionOptions
pub fn extensions(options: &crate::ext::ExtensionOptions, _is_snapshot: bool) -> Vec<Extension> {
    vec![never_jscore_random::init(options.random_seed)]
}

/// Get JavaScript initialization code for random extension
/// This overrides Math.random() to use the seeded RNG
pub fn get_init_js() -> &'static str {
    include_str!("init_random.js")
}
