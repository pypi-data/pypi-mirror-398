#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

# ignite_install_headers(FILES <header>... DESTINATION <dest>)
#
# Function to install header files.
function(ignite_install_headers)
    cmake_parse_arguments(IGNITE_INSTALL "" "DESTINATION" "FILES" ${ARGN})

    foreach(HEADER ${IGNITE_INSTALL_FILES})
        get_filename_component(SUBDIR ${HEADER} DIRECTORY)
        install(FILES ${HEADER} DESTINATION ${IGNITE_INSTALL_DESTINATION}/${SUBDIR} COMPONENT Development)
    endforeach()
endfunction()
