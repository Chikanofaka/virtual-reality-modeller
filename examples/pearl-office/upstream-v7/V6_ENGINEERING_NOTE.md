# V6 engineering correction

The Safari screenshots proved that rendering + drag-look are healthy. The remaining failure was locomotion/navigation.

Two root causes were corrected:

- **Invisible/disconnected floor:** the large `ShapeGeometry` floor was rotated `+PI/2`, which turns its front face downward. With single-sided material, the continuous floor was back-face culled from the player's viewpoint; only local room pads remained visible. V6 rotates it `-PI/2`.
- **Visual geometry was still too coupled to navigation:** V6 defines a continuous walkable navmesh independent of decorative and room meshes. This keeps the main-repo model but makes the outer loop traversable.

Safari remains the preferred runtime because it already demonstrated continuous frame presentation for click-drag look on this Mac.
