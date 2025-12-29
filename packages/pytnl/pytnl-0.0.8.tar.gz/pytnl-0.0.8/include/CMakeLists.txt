if (SKBUILD_DATA_DIR)
    install( DIRECTORY pytnl DESTINATION "${SKBUILD_DATA_DIR}/${CMAKE_INSTALL_INCLUDEDIR}"
             FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp" )
else()
    install( DIRECTORY pytnl TYPE INCLUDE
             FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp" )
endif()
