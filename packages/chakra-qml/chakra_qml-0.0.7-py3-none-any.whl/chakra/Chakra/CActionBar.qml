import QtQuick
import QtQuick.Effects

/*
    CActionBar - 操作栏组件（批量操作浮动栏）

    == 组件库特有属性 ==
    open           : 是否显示，默认 false
    selectionCount : 选中数量，默认 0

    == 信号 ==
    closed           : 关闭时触发
    selectAllClicked : 全选按钮点击时触发
*/
Item {
    id: root

    // 是否显示
    property bool open: false

    // 选中数量
    property int selectionCount: 0

    // 内容
    default property alias content: contentRow.data

    // 关闭信号
    signal closed

    // 全选信号
    signal selectAllClicked

    anchors.left: parent ? parent.left : undefined
    anchors.right: parent ? parent.right : undefined
    anchors.bottom: parent ? parent.bottom : undefined
    anchors.margins: AppStyle.spacing4
    height: 56

    // 动画控制
    opacity: open ? 1 : 0
    visible: opacity > 0
    transform: Translate {
        y: root.open ? 0 : 20
    }

    Behavior on opacity {
        NumberAnimation {
            duration: AppStyle.durationNormal
            easing.type: Easing.OutCubic
        }
    }

    Behavior on transform {
        NumberAnimation {
            duration: AppStyle.durationNormal
            easing.type: Easing.OutCubic
        }
    }

    // 主容器
    Rectangle {
        id: container
        anchors.centerIn: parent
        width: contentRow.width + AppStyle.spacing4 * 2
        height: parent.height
        radius: AppStyle.radiusLg
        color: AppStyle.surfaceColor
        border.width: 1
        border.color: AppStyle.borderColor

        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: "#30000000"
            shadowBlur: 1.0
            shadowVerticalOffset: 8
            shadowHorizontalOffset: 0
        }

        Row {
            id: contentRow
            anchors.centerIn: parent
            spacing: AppStyle.spacing2

            // 选中数量显示
            Text {
                visible: root.selectionCount > 0
                text: root.selectionCount + " 项已选中"
                font.pixelSize: AppStyle.fontSizeSm
                font.weight: Font.Medium
                color: AppStyle.textSecondary
                anchors.verticalCenter: parent.verticalCenter
            }

            // 分隔线
            Rectangle {
                visible: root.selectionCount > 0
                width: 1
                height: 24
                color: AppStyle.borderColor
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
