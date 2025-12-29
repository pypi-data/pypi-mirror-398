add_subdirectory( pytnl )

# Install all Python files to site-packages
install(
    DIRECTORY pytnl
    DESTINATION ${PyTNL_PYTHON_SITE_PACKAGES_DIR}
    FILES_MATCHING
    PATTERN "*.py"
)
