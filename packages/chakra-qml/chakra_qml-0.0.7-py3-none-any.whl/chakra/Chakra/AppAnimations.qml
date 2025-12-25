pragma Singleton
import QtQuick

QtObject {
    // 动画时长
    readonly property int durationFast: 100
    readonly property int durationNormal: 150
    readonly property int durationSlow: 300

    // 缓动函数
    readonly property int easingStandard: Easing.OutQuad
    readonly property int easingBounce: Easing.OutBack
    readonly property int easingSmooth: Easing.InOutQuad

    // 按钮动效参数
    readonly property real buttonPressScale: 0.97
    readonly property real buttonTextPressScale: 0.95
    readonly property real buttonHoverBrightness: 1.15
    readonly property real buttonPressDarkness: 1.3

    // 输入框动效参数
    readonly property int inputFocusBorderWidth: 2
    readonly property int inputNormalBorderWidth: 1

    // 通用缩放
    readonly property real hoverScale: 1.02
    readonly property real pressScale: 0.98
}
