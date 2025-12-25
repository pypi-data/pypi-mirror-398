/*
*  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <gtest/gtest.h>

namespace ignite::detail {
/**
 * Wrapper for default GTest event listener responsible for xml report.
 * We override test suite name to include version information in order to distinguish results on TeamCity output.
 * GTest do not provide any API to manipulate test information so some hacks were introduced
 * at ignite::detail::ignite_xml_unit_test_result_printer::OnTestIterationEnd
 * Name requirement for test suite is enforced: test suite should end with '_ign_version' which would be replaced
 * with actual version in xml report.
 */
class ignite_xml_unit_test_result_printer : public ::testing::EmptyTestEventListener {
    TestEventListener *m_delegate;
    std::string m_version;
public:
    ignite_xml_unit_test_result_printer(::testing::TestEventListener *delegate, std::string version);

    ~ignite_xml_unit_test_result_printer() override {
        delete m_delegate;
    }

    void OnTestProgramStart(const testing::UnitTest &) override;
    void OnTestIterationStart(const testing::UnitTest &, int) override;
    void OnEnvironmentsSetUpStart(const testing::UnitTest &) override;
    void OnEnvironmentsSetUpEnd(const testing::UnitTest &) override;
    void OnTestSuiteStart(const testing::TestSuite &) override;
    void OnTestCaseStart(const testing::TestCase &) override;
    void OnTestStart(const testing::TestInfo &) override;
    void OnTestDisabled(const testing::TestInfo &) override;
    void OnTestPartResult(const testing::TestPartResult &) override;
    void OnTestEnd(const testing::TestInfo &) override;
    void OnTestSuiteEnd(const testing::TestSuite &) override;
    void OnTestCaseEnd(const testing::TestCase &) override;
    void OnEnvironmentsTearDownStart(const testing::UnitTest &) override;
    void OnEnvironmentsTearDownEnd(const testing::UnitTest &) override;
    void OnTestIterationEnd(const testing::UnitTest &, int) override;
    void OnTestProgramEnd(const testing::UnitTest &) override;
};
} // namespace ignite::detail