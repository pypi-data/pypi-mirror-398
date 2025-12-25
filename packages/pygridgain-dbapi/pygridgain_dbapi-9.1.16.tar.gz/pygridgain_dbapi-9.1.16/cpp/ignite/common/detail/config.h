/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#ifndef __has_include
# define __has_include(x) 0
#endif

#if __has_include(<version>)
# include <version>
#endif

#ifndef __has_attribute
# define __has_attribute(x) 0
#endif

#if defined(_WIN32)
# define IGNITE_CALL __stdcall
# define IGNITE_EXPORT __declspec(dllexport)
# define IGNITE_IMPORT __declspec(dllimport)
#else
# define IGNITE_CALL
# if __has_attribute(visibility) || (defined(__GNUC__) && ((__GNUC__ > 4) || (__GNUC__ == 4) && (__GNUC_MINOR__ > 2)))
#  define IGNITE_EXPORT __attribute__((visibility("default")))
#  define IGNITE_IMPORT __attribute__((visibility("default")))
# else
#  define IGNITE_EXPORT
#  define IGNITE_IMPORT
# endif
#endif

#ifdef IGNITE_IMPL
# define IGNITE_API IGNITE_EXPORT
#else
# define IGNITE_API IGNITE_IMPORT
#endif

/**
 * Macro IGNITE_SWITCH_WIN_OTHER that uses first option on Windows and second on any other OS.
 */
#ifdef WIN32
# define IGNITE_SWITCH_WIN_OTHER(x, y) x
#else
# define IGNITE_SWITCH_WIN_OTHER(x, y) y
#endif

#ifndef UNUSED_VALUE
# define UNUSED_VALUE (void)
#endif // UNUSED_VALUE
