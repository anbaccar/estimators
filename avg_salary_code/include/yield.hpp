#ifndef YIELD_H_
#define YIELD_H_


#include <algorithm>
#include <coroutine>
using namespace std;

template <typename ENCAPSULATED_TYPE>
struct generator {
    struct promise_type;
    using coro_handle = std::coroutine_handle<promise_type>;
    struct promise_type {
        ENCAPSULATED_TYPE current_value;

        auto get_return_object() { return generator{coro_handle::from_promise(*this)}; }
        auto initial_suspend() { return std::suspend_always{}; }
        auto final_suspend() noexcept { return std::suspend_always{}; }
        void unhandled_exception() { std::terminate(); }

        template <typename T>
        auto yield_value(T &value) {
            current_value = value;
            return std::suspend_always{};
        }
    };
    bool move_next() { return coro ? (coro.resume(), !coro.done()) : false; }
    ENCAPSULATED_TYPE current_value() { return coro.promise().current_value; }
    generator(generator const &) = delete;
    generator(generator &&rhs) : coro(rhs.coro) { rhs.coro = nullptr; }
    ~generator() {
        if (coro)
            coro.destroy();
    }

private:
    generator(coro_handle h) : coro(h) {}
    coro_handle coro;
};

#endif