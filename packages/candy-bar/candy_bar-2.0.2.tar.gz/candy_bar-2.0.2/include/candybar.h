#include <cstdint>
#include <string>
#include <chrono>
#include <optional>
#include <mutex>

class CandyBar
{
    /**
     * A simple pacman-inspired progress bar
     */
    public:
        explicit CandyBar(uint32_t total,
                          std::string_view message = "",
                          std::optional<uint32_t> messageWidth = std::nullopt,
                          std::optional<uint32_t> width = std::nullopt,
                          uint32_t linePos = 0,
                          bool leftJustified = true,
                          bool disable = false);

        /**
         * @brief Disable the progress bar
         * @param[in] disable : disable flag value
         */
        void disable(bool disable = true) noexcept;

        /**
         * @brief Set the total value of the progress bar
         * @param[in] total : new total value
         */
        void setTotal(uint32_t total) noexcept;

        /**
         * @brief Get the total value of the progress bar
         * @returns[uint32_t] The current total value
         */
        inline uint32_t getTotal() const { return m_totalValue; };

        /**
         * @brief Set the line position of the progress bar
         * @param[in] pos : new position value
         */
        void setLinePos(uint32_t pos) noexcept;

        /**
         * @brief Get the line position of the progress bar
         * @returns[uint32_t] The line position of the progress bar
         */
        inline uint32_t getLinePos() const { return m_linePos; };

        /**
         * @brief Set the new message for the progress bar
         * @param[in] message : new message
         */
        void setMessage(std::string_view message, std::optional<uint32_t> messageWidth = std::nullopt) noexcept;

        /**
         * @brief Enable/disable left justification
         * @param[in] value : left justification flag
         */
        void setLeftJustified(bool value = true);

        /**
         * @brief Update the progress bar with the new value
         * @param[in] current : current value
         */
        void update(uint32_t current);

    private:
        void get_terminal_width(int& width);
        uint32_t m_totalValue;
        uint32_t m_pgWidth;
        uint32_t m_linePos;
        uint32_t m_messageSize{0};
        std::string m_message;
        bool m_verbose;
        bool m_leftJustified;
        std::chrono::steady_clock::time_point m_lastUpdate;
        uint32_t m_emaDurationNs;
        mutable std::mutex m_lock;

        void initialize(std::optional<uint32_t> width);

        std::optional<uint32_t> computeEtSec(uint32_t currentValue);
        void render(uint32_t currentValue, std::optional<uint32_t> eta);
        std::string formatEta(std::optional<uint32_t> eta) const;

};
