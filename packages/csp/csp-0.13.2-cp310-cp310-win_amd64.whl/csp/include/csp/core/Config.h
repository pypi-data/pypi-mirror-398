/* #undef CSP_VERSION_MAJOR */
#define CSP_VERSION_MINOR
#define CSP_VERSION_PATCH
#define CSP_VERSION ((CSP_VERSION_MAJOR * 1000) + CSP_VERSION_MINOR) * 1000 + CSP_VERSION_PATCH

// in case we need this in plugins
#define CSP_ABI_VERSION CSP_VERSION_MAJOR

/* #undef CSP_BUILD_TYPE */

