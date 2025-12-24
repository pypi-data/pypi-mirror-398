
#version 330

struct Light {
    vec3 position;
    vec3 color;
    float intensity;
};

#define MAX_LIGHTS 8
uniform int num_lights;
uniform Light lights[MAX_LIGHTS];
uniform float ambient;
uniform sampler2DShadow shadow_map;

in vec3 frag_pos;
in vec3 frag_normal;
in vec3 frag_color;
in vec4 frag_pos_light_space;

out vec4 f_color;

// ---- internal tuning (shader-only, tweak visually) ----
const float LIGHT_SIZE_APPROX = 0.25; // tune for larger/smaller penumbrae (shader-only)
const int BLOCKER_SEARCH_RADIUS = 2;  // coarse search radius (in samples; 2 -> 5x5)
const int PCF_MAX_RADIUS = 6;         // max PCF radius (in samples; 6 -> 13x13 kernel max)
const float MIN_BIAS = 0.0005;
const float MAX_BIAS_SCALE = 0.005;

void main() {
    vec3 normal = normalize(frag_normal);
    vec3 color = frag_color / 255.0;
    vec3 result = ambient * color;

    for (int i = 0; i < num_lights; i++) {
        vec3 light_dir = normalize(lights[i].position - frag_pos);

        // ----- Physically-correct attenuation -----
        float dist = length(lights[i].position - frag_pos);
        float attenuation = 1.0 / (dist * dist + 0.001);

        // ----- Diffuse (Lambert) -----
        float diff = max(dot(normal, light_dir), 0.0);

        // ----- Specular (Blinn-Phong) -----
        vec3 view_dir = normalize(-frag_pos); // camera at origin for now
        vec3 half_dir = normalize(light_dir + view_dir);

        float shininess = 32.0;
        float spec = pow(max(dot(normal, half_dir), 0.0), shininess);

        // ----- Shadow (PCSS-like approximation using sampler2DShadow only) -----
        vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
        proj_coords = proj_coords * 0.5 + 0.5;

        float shadow = 1.0;

        if (proj_coords.x >= 0.0 && proj_coords.x <= 1.0 &&
        proj_coords.y >= 0.0 && proj_coords.y <= 1.0) {

            // normal-dependent bias
            float ndotl = dot(normal, light_dir);
            float bias = max(MAX_BIAS_SCALE * (1.0 - ndotl), MIN_BIAS);

            ivec2 texSize = textureSize(shadow_map, 0);
            float texelSizeX = 1.0 / float(texSize.x);
            float texelSizeY = 1.0 / float(texSize.y);

            // --- 1) Blocker search (coarse). Count how many samples are blockers.
            int searchCount = 0;
            int blockerCount = 0;

            for (int sx = -BLOCKER_SEARCH_RADIUS; sx <= BLOCKER_SEARCH_RADIUS; ++sx) {
                for (int sy = -BLOCKER_SEARCH_RADIUS; sy <= BLOCKER_SEARCH_RADIUS; ++sy) {
                    vec2 offset = vec2(float(sx) * texelSizeX, float(sy) * texelSizeY);
                    // texture(shadow_map, vec3(uv, refDepth)) returns 1.0 if lit, 0.0 if blocked
                    float cmp = texture(shadow_map, vec3(proj_coords.xy + offset, proj_coords.z - bias));
                    searchCount++;
                    if (cmp < 0.5) { // considered a blocker
                        blockerCount++;
                    }
                }
            }

            // If no blockers, fully lit (no shadow)
            if (blockerCount == 0) {
                shadow = 1.0;
            } else {
                // --- 2) Compute a penumbra radius from blocker ratio and distance
                // blockerRatio ranges 0..1
                float blockerRatio = float(blockerCount) / float(searchCount);

                // Map blockerRatio -> radius in texel samples (approx)
                // Larger distance increases apparent penumbra; scale by LIGHT_SIZE_APPROX and dist
                float radiusFactor = clamp(blockerRatio, 0.0, 1.0);
                // base radius mapped from ratio
                float baseRadius = mix(1.0, float(PCF_MAX_RADIUS), radiusFactor);

                // scale with fragment-to-light distance (tuneable)
                float distScale = clamp(dist / 10.0, 0.5, 4.0);
                float radiusSamples = clamp(baseRadius * distScale * LIGHT_SIZE_APPROX * 4.0, 1.0, float(PCF_MAX_RADIUS));

                // normalize radius to [0,1] relative to PCF_MAX_RADIUS to scale offsets
                float radiusNorm = radiusSamples / float(PCF_MAX_RADIUS);

                // --- 3) Final PCF using scaled sampling kernel (fixed loop bounds but scaled offsets)
                // We'll sample a (2*PCF_MAX_RADIUS+1)^2 kernel and scale sample offsets by radiusNorm
                float sum = 0.0;
                float count = 0.0;

                for (int x = -PCF_MAX_RADIUS; x <= PCF_MAX_RADIUS; ++x) {
                    for (int y = -PCF_MAX_RADIUS; y <= PCF_MAX_RADIUS; ++y) {
                        // scale offsets by radiusNorm so effective kernel size changes dynamically
                        vec2 offset = vec2(float(x) * texelSizeX * radiusNorm,
                        float(y) * texelSizeY * radiusNorm);
                        sum += texture(shadow_map, vec3(proj_coords.xy + offset, proj_coords.z - bias));
                        count += 1.0;
                    }
                }

                shadow = sum / count;

                // Slightly smooth the final shadow value to avoid hard quantization
                shadow = smoothstep(0.0, 1.0, shadow);
            }
        }

        // ----- Final Lighting -----
        vec3 lightColor = lights[i].color * lights[i].intensity;

        vec3 diffuse = diff * lightColor * attenuation;
        vec3 specular = spec * lightColor * attenuation;

        result += shadow * (diffuse + specular) * color;
    }

    f_color = vec4(result, 1.0);
}
