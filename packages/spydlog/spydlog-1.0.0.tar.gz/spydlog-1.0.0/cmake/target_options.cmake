function(set_target_options target_name)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64|ARM64)")
        set(IS_ARM TRUE)
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)")
        set(IS_ARM FALSE)
    else()
        set(IS_ARM FALSE)
        message(WARNING "Unknown processor architecture: ${CMAKE_SYSTEM_PROCESSOR}, assuming x86_64")
    endif()

    if(CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
        if(${SANITIZE})
            target_compile_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=address>)
            target_link_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=address>)
            target_compile_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=undefined>)
            target_link_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=undefined>)
        endif()

        set(COMPILE_OPTIONS -D_FORTIFY_SOURCE=2 -pipe -Wall -pedantic-errors $<$<CONFIG:Release,RelWithDebInfo>:-O3>)

        if(IS_ARM)
            if(CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
            else()
                # For non-Apple ARM (Linux ARM64), enable NEON
                list(APPEND COMPILE_OPTIONS -march=armv8-a+fp+simd)
            endif()
        else()
            if(CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
                list(APPEND COMPILE_OPTIONS -mavx2 -mfma)
            else()
                list(APPEND COMPILE_OPTIONS $<$<CONFIG:Release,RelWithDebInfo>:-ftree-vectorizer-verbose=2> -mveclibabi=svml -mavx2 -mfma)
            endif()
        endif()

        target_compile_options(${target_name} PRIVATE ${COMPILE_OPTIONS})

    elseif(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        if(${SANITIZE})
            target_compile_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=address>)
            target_link_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=address>)
            target_compile_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=undefined>)
            target_link_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:-fsanitize=undefined>)
        endif()

        set(COMPILE_OPTIONS -D_FORTIFY_SOURCE=2 -pipe -Wall -pedantic-errors $<$<CONFIG:Release,RelWithDebInfo>:-O3 -ftree-vectorizer-verbose=2>)

        if(IS_ARM)
            list(APPEND COMPILE_OPTIONS -march=armv8-a+fp+simd -mtune=generic)
        else()
            list(APPEND COMPILE_OPTIONS -mveclibabi=svml -mavx2 -mfma)
        endif()

        target_compile_options(${target_name} PRIVATE ${COMPILE_OPTIONS})

    elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Intel")
        message(FATAL_ERROR "Intel compiler is not supported")

    elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
        if(${SANITIZE})
            target_compile_options(${target_name} PRIVATE $<$<CONFIG:Debug,RelWithDebInfo>:/fsanitize=address>)
        endif()

        set(COMPILE_OPTIONS /W4 /utf-8 $<$<CONFIG:Release,RelWithDebInfo>:/O2 /GF /Ot /Oy /GT /GL /Oi /Zi /Gm- /Zc:inline>)

        if(IS_ARM)
            # MSVC ARM64 optimizations are mostly automatic
        else()
            include(find_avx)
            list(APPEND COMPILE_OPTIONS ${AVX_FLAGS})
        endif()

        target_compile_options(${target_name} PRIVATE ${COMPILE_OPTIONS})
    else()
        message(WARNING "Unknown compiler: ${CMAKE_CXX_COMPILER_ID}, using minimal options")
        set(COMPILE_OPTIONS -O3 -Wall)
        target_compile_options(${target_name} PRIVATE ${COMPILE_OPTIONS})
    endif()

    # Provides the macro definition DEBUG_BUILD
    target_compile_definitions(${target_name} PRIVATE $<$<CONFIG:Debug>:DEBUG_BUILD>)
endfunction()
