import QtQuick

/*
    CSpinner - 加载指示器组件

    == 组件库特有属性 ==
    size        : 尺寸，可选 "xs" | "sm" | "md" | "lg" | "xl"，默认 "md"
    colorScheme : 颜色方案，默认 "primary"
    color       : 自定义颜色（覆盖 colorScheme）
*/
Item {
    id: root

    // 尺寸: xs, sm, md, lg, xl
    property string size: "md"

    // 颜色方案
    property string colorScheme: "primary"

    // 计算颜色
    property color color: AppStyle.getSchemeColor(colorScheme)

    // 线条粗细
    property int thickness: AppStyle.getSpinnerThickness(size)
    property int spinnerSize: AppStyle.getSpinnerSize(size)

    implicitWidth: spinnerSize
    implicitHeight: spinnerSize

    Canvas {
        id: canvas
        anchors.fill: parent

        property real angle

        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();

            var centerX = width / 2;
            var centerY = height / 2;
            var radius = Math.min(width, height) / 2 - root.thickness;

            // 绘制圆弧
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, angle, angle + Math.PI * 1.5);
            ctx.strokeStyle = root.color;
            ctx.lineWidth = root.thickness;
            ctx.lineCap = "round";
            ctx.stroke();
        }

        NumberAnimation on angle {
            from: 0
            to: Math.PI * 2
            duration: 1000
            loops: Animation.Infinite
            running: root.visible
        }

        onAngleChanged: requestPaint()
    }
}
