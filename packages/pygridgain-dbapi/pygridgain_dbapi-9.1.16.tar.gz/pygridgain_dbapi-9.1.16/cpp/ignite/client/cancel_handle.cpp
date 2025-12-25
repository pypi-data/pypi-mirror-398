/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/cancel_handle.h"
#include "ignite/client/detail/cancellation_token_impl.h"

namespace ignite
{

/**
 * @brief Implementation for cancellation handle.
 *
 * Implementation of @ref ignite::cancel_handle.
 */
class cancel_handle_impl : public cancel_handle
{
public:
    /**
     * Constructor.
     */
    cancel_handle_impl()
        : m_token(std::make_shared<cancellation_token_impl>()) { }

    /**
     * Destructor.
     */
    ~cancel_handle_impl() override = default;

    /**
     * Abruptly terminates an execution of an associated process.
     *
     * @param callback A callback that will be called after the process has been terminated and the resources associated
     *                 with that process have been freed.
     */
    IGNITE_API void cancel_async(ignite_callback<void> callback) override {
        m_token->cancel_async(std::move(callback));
    }

    /**
     * Flag indicating whether cancellation was requested or not.
     *
     * This method will return true even if cancellation has not been completed yet.
     *
     * @return @c true if the cancellation was requested.
     */
    IGNITE_API bool is_cancelled() const override { return m_token->is_cancelled(); }

    /**
     * Issue a token associated with this handle.
     *
     * Token is reusable, meaning the same token may be used to link several executions into a single cancellable.
     *
     * @return A token associated with this handle.
     */
    IGNITE_API std::shared_ptr<cancellation_token> get_token() override {
        return m_token;
    }

private:
    /** Cancellation token. */
    std::shared_ptr<cancellation_token_impl> m_token;
};


std::shared_ptr<cancel_handle> cancel_handle::create() {
    return std::make_shared<cancel_handle_impl>();
}

} // namespace ignite
