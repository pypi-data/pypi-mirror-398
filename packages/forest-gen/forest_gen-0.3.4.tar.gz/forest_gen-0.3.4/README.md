# forest_gen

Showcase forest scene generation module utilizing
[stripe_kit](https://github.com/GrafCzterech/STRIPE-kit). It's rather generic,
should allow you to generate all kinds of forests, but it is entirely focused
on generating forests.

The core functionality, to be used with `stripe_kit` is isolated as
`forest_gen`. Trying to import that module without running IsaacLab will result
in an error. The auxiliary logic for forest generation is isolated as
`forest_gen_utils`, and feel free to import it in non-IsaacLab environments.
