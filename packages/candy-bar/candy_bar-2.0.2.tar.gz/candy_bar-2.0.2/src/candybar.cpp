#include "candybar.h"
#include <print>
#include <algorithm>
#include <cctype>
#include <iostream>

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#define VC_EXTRALEAN
#include <Windows.h>
#elif defined(__linux__)
#include <sys/ioctl.h>
#include <unistd.h>
#endif // Windows/Linux

namespace
{
constexpr double emaAlpha{0.1};
constexpr uint32_t secondsPerMinute{60};
constexpr uint32_t secondsPerHour{3600};
constexpr uint32_t minPgWidth{50};
constexpr uint32_t minBarWidth{25};
constexpr uint32_t candySpacing{3};


uint32_t getTerminalWidth()
{
    constexpr uint32_t defaultSize{80};
#if defined(_WIN32)
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    if (GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &csbi))
    {
        return static_cast<uint32_t>(csbi.srWindow.Right - csbi.srWindow.Left + 1);
    }
#elif defined(__linux__)
    struct winsize w;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &w) == 0)
    {
        return static_cast<uint32_t>(w.ws_col);
    }
#endif
    return defaultSize;
}

std::string stripLTWhitespaces(std::string_view str)
{
    // Find the first non-whitespace character
    auto start = std::find_if_not(str.begin(), str.end(), [](unsigned char ch) {
        return std::isspace(ch);
    });

    // Find the last non-whitespace character
    auto end = std::find_if_not(str.rbegin(), str.rend(), [](unsigned char ch) {
        return std::isspace(ch);
    }).base();

    // Return the substring that excludes leading and trailing whitespaces
    return (start < end) ? std::string(start, end) : std::string();
}
}

CandyBar::CandyBar(uint32_t total,
                   std::string_view message,
                   std::optional<uint32_t> messageWidth,
                   std::optional<uint32_t> width,
                   uint32_t linePos,
                   bool leftJustified,
                   bool disable)
    : m_totalValue(total), m_pgWidth(0), m_verbose(!disable), m_leftJustified(leftJustified),
      m_lastUpdate(std::chrono::steady_clock::now()), m_emaDurationNs(0)
{
    setMessage(message, messageWidth);
    setLinePos(linePos);
    initialize(width);
}

void CandyBar::initialize(std::optional<uint32_t> width)
{

    if (width.has_value())
    {
        m_pgWidth = width.value();
    }
    else
    {
        m_pgWidth = getTerminalWidth();
    }

    if (m_pgWidth < minPgWidth)
    {
        throw std::range_error(std::format("Progress Bar width is {} is too small", minPgWidth));
        return;
    }

}

void CandyBar::setTotal(uint32_t total) noexcept
{
    std::unique_lock lock(m_lock);
    // Set the total value
    m_totalValue = total;
}

void CandyBar::disable(bool disable) noexcept
{
    std::unique_lock lock(m_lock);
    m_verbose = !disable;
}

void CandyBar::setLinePos(uint32_t pos) noexcept
{
    std::unique_lock lock(m_lock);

    m_linePos = pos;
    if (m_verbose && m_linePos > 0)
    {
        for (uint32_t i = 0; i < m_linePos; ++i)
        {
            std::println("");
        }
    }
}

void CandyBar::setMessage(std::string_view message, std::optional<uint32_t> messageWidth) noexcept
{
    std::unique_lock lock(m_lock);

    m_message = stripLTWhitespaces(message);

    if (messageWidth.has_value() && messageWidth.value() != 0)
    {
        auto msgSize{messageWidth.value()};
        const auto sizeDelta{m_leftJustified ? 0 : 1};
        if (msgSize - sizeDelta < m_message.length())
        {
            std::print("Provided message does not fit into the requested space {}. Increasing ...\n", msgSize);
            msgSize = m_message.length() + sizeDelta;
        }
        m_messageSize = msgSize;

        if (m_leftJustified)
        {
            m_message = std::format("{:<{}}", message, msgSize);
        }
        else
        {
            m_message = std::format("{:>{}} ", message, msgSize - 1);
        }
    }
    else
    {
        m_message += ' ';
    }
}

void CandyBar::setLeftJustified(bool value)
{
    {
        std::unique_lock lock(m_lock);
        // Change the justification
        m_leftJustified = value;
    }
    this->setMessage(stripLTWhitespaces(m_message), m_messageSize);
}

std::optional<uint32_t> CandyBar::computeEtSec(uint32_t currentValue)
{
    // Get the current time
    const auto now{std::chrono::steady_clock::now()};
    const auto duration{std::chrono::duration_cast<std::chrono::nanoseconds>(now - m_lastUpdate)};

    if (m_emaDurationNs == 0)
    {
        // First sample - initialize with actual duration
        m_emaDurationNs = static_cast<uint32_t>(duration.count());
        return std::nullopt;
    }
    else
    {
        // EMA formula: new_avg = α * new_value + (1 - α) * old_avg
        m_emaDurationNs = emaAlpha * duration.count() + (1.0 - emaAlpha) * m_emaDurationNs;
        m_lastUpdate = now;
    }
    // Calculate ETA
    const uint32_t remainingItems{m_totalValue - currentValue};
    const double timePerIteration{m_emaDurationNs / 1'000'000'000.0};
    const uint32_t eta{static_cast<uint32_t>(remainingItems * timePerIteration)};

    return eta;
}

void CandyBar::update(uint32_t current)
{
    std::unique_lock lock(m_lock);

    if (current > m_totalValue)
    {
        current = m_totalValue;
    }

    const auto eta{computeEtSec(current)};

    // Don't show the progress bar if disabled
    if (m_verbose)
    {
        render(current, eta);
    }
}

std::string CandyBar::formatEta(std::optional<uint32_t> eta) const
{
        if (!eta.has_value())
        {
            return "[--:--]";
        }

        uint32_t remainingSec(eta.value());

        if (remainingSec >= secondsPerHour)
        {
            const uint32_t hours{remainingSec / secondsPerHour};
            remainingSec %= secondsPerHour;
            const uint32_t mins{remainingSec / secondsPerMinute};
            remainingSec %= secondsPerMinute;
            return std::format("[{}:{:02d}:{:02d}]", hours, mins, remainingSec);
        }

        if (remainingSec >= secondsPerMinute) {
            const uint32_t mins{remainingSec / secondsPerMinute};
            remainingSec %= secondsPerMinute;
            return std::format("[{}:{:02d}]", mins, remainingSec);
        }

        return std::format("[0:{:02d}]", remainingSec);
}

void CandyBar::render(uint32_t currentValue, std::optional<uint32_t> eta)
{
    const float progress{static_cast<float>(currentValue) / m_totalValue};
    const auto etaStr{formatEta(eta)};
    const auto endStr{std::format("] {:3d}%", static_cast<uint32_t>(progress * 100.0f))};

    std::string pg;
    pg.reserve(m_pgWidth);

    if (m_pgWidth - (etaStr.length() + endStr.length() + 1) > minBarWidth)
    {
        pg += m_message;
    }

    // Add the ETA string
    pg += etaStr;

    // Draw progress bar
    pg += '[';
    const size_t barWidth{m_pgWidth - (pg.length() + endStr.length())};
    const size_t currentPos{static_cast<size_t>(barWidth * progress)};

    const char markerChar{(currentPos % candySpacing == (candySpacing - 1)) ? 'C' : 'c'};
    for (size_t i{0}; i < barWidth; ++i)
    {
        if (i < currentPos)
        {
            pg += '-';
        }
        else if (i == currentPos)
        {
            // Pacman animation
            pg += std::format("\e[1;33m{}\e[0m", markerChar);
        }
        else
        {
            // Candy dots
            pg += ((i % candySpacing == 0) ? 'o' : ' ');
        }
    }

    if (m_linePos != 0)
    {
        std::print("\033[{}A", m_linePos);
    }

    std::print("\r{}{}", pg, endStr);

    if (m_linePos != 0)
    {
        std::print("\033[{}B", m_linePos);  // Move down
    }

    std::cout.flush();
}
