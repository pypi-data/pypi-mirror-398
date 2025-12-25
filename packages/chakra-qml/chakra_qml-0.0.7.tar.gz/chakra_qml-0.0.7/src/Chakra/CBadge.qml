pragma ComponentBehavior: Bound

import QtQuick

/*
    CBadge - 徽章组件

    == 组件库特有属性 ==
    colorScheme : 颜色方案，可选 "primary" | "success" | "warning" | "error" | "gray" 等，默认 "primary"
    variant     : 变体，可选 "solid" | "subtle" | "outline"，默认 "subtle"
    size        : 尺寸，可选 "sm" | "md" | "lg"，默认 "md"
    text        : 徽章文本，默认 ""
*/
Rectangle {
    id: root

    // 颜色方案: primary, secondary, success, warning, error, gray
    property string colorScheme: "primary"

    // 变体: solid, subtle, outline
    property string variant: "subtle"

    // 尺寸: sm, md, lg
    property string size: "md"

    // 文本
    property string text: ""

    property color schemeColor: AppStyle.getSchemeColor(colorScheme)

    property color schemeBgColor: {
        switch (colorScheme) {
        case "success":
            return AppStyle.successLight;
        case "warning":
            return AppStyle.warningLight;
        case "error":
            return AppStyle.errorLight;
        default:
            return Qt.rgba(schemeColor.r, schemeColor.g, schemeColor.b, 0.15);
        }
    }

    property int fontSize: AppStyle.getBadgeFontSize(size)
    property int paddingH: AppStyle.getPaddingH(size)
    property int paddingV: size === "sm" ? 2 : (size === "lg" ? AppStyle.spacing2 : AppStyle.spacing1)

    implicitWidth: label.implicitWidth + paddingH * 2
    implicitHeight: label.implicitHeight + paddingV * 2

    radius: AppStyle.radiusSm

    color: {
        if (root.variant === "solid")
            return root.schemeColor;
        if (root.variant === "subtle")
            return root.schemeBgColor;
        return "transparent";
    }

    border.width: root.variant === "outline" ? 1 : 0
    border.color: root.schemeColor

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text.toUpperCase()
        font.pixelSize: root.fontSize
        font.weight: Font.Bold
        font.letterSpacing: 0.5
        color: {
            if (root.variant === "solid")
                return AppStyle.textLight;
            return root.schemeColor;
        }
    }
}
