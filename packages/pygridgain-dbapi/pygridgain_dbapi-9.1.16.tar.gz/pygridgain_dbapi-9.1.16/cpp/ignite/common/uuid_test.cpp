/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "uuid.h"

#include <gtest/gtest.h>

#include <sstream>

TEST(uuid, construct) {
    {
        ignite::uuid uuid;
        EXPECT_EQ(0, uuid.get_most_significant_bits());
        EXPECT_EQ(0, uuid.get_least_significant_bits());
    }
    {
        ignite::uuid uuid(1, 2);
        EXPECT_EQ(1, uuid.get_most_significant_bits());
        EXPECT_EQ(2, uuid.get_least_significant_bits());
    }
    {
        ignite::uuid uuid(1, 2);
        ignite::uuid uuid2(uuid);
        EXPECT_EQ(1, uuid2.get_most_significant_bits());
        EXPECT_EQ(2, uuid2.get_least_significant_bits());
        EXPECT_EQ(uuid, uuid2);
    }
}

TEST(uuid, stream) {
    std::string uuidString = "123e4567-e89b-12d3-a456-426614174000";

    std::stringstream stream;
    stream << uuidString;

    ignite::uuid uuid;
    stream >> uuid;

    EXPECT_EQ(0x123e4567e89b12d3, uuid.get_most_significant_bits());
    EXPECT_EQ(0xa456426614174000, uuid.get_least_significant_bits());

    EXPECT_EQ(1, uuid.version());
    EXPECT_EQ(2, uuid.variant());

    std::stringstream stream2;
    stream2 << uuid;

    std::string uuidString2;
    stream2 >> uuidString2;

    EXPECT_EQ(uuidString, uuidString2);
}
