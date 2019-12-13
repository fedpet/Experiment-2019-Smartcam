package it.unibo.alchemist.boundary.gui.effects;

import it.unibo.alchemist.boundary.wormhole.interfaces.IWormhole2D;
import it.unibo.alchemist.model.implementations.actions.See;
import it.unibo.alchemist.model.implementations.molecules.SimpleMolecule;
import it.unibo.alchemist.model.implementations.positions.Euclidean2DPosition;
import it.unibo.alchemist.model.interfaces.Environment;
import it.unibo.alchemist.model.interfaces.Node;
import it.unibo.alchemist.model.interfaces.Position;
import it.unibo.alchemist.model.interfaces.Position2D;
import it.unibo.alchemist.model.interfaces.environments.EuclideanPhysics2DEnvironment;
import it.unibo.alchemist.model.interfaces.geometry.AwtShapeCompatible;
import it.unibo.alchemist.model.interfaces.geometry.GeometricShape;

import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.geom.Arc2D;

/**
 * USED FOR THE THESIS PRESENTATION.
 * Draws everything with fixed sizes, good for the projector.
 */
public final class DrawForPresentation implements Effect {
    private static final SimpleMolecule WANTED = new SimpleMolecule("wanted");
    private static final SimpleMolecule VISION = new SimpleMolecule("vision");
    private static final Color COLOR_WANTED = new Color(200,0,0);
    private static final Color COLOR_OBJECT = new Color(0,150,0);
    private static final Color COLOR_CAMERA = Color.BLACK;
    private static final Color COLOR_FOV = Color.BLUE;
    private static final double CAM_SHAPE_SIZE = 2.5;
    private static final double OBJ_SHAPE_SIZE = 4;
    private static final long serialVersionUID = 1L;

    @Override
    public <T, P extends Position2D<P>> void apply(Graphics2D g, Node<T> node, Environment<T, P> environment, IWormhole2D<P> wormhole) {
        if (environment instanceof EuclideanPhysics2DEnvironment) {
            @SuppressWarnings("unchecked") final EuclideanPhysics2DEnvironment<T> env = (EuclideanPhysics2DEnvironment<T>) environment;
            final Point viewPoint = wormhole.getViewPoint(environment.getPosition(node));
            final int x = viewPoint.x;
            final int y = viewPoint.y;
            drawShape(g, node, env, wormhole.getZoom(), x, y);
            drawFieldOfView(g, node, env, wormhole.getZoom(), x, y);
        }
    }

    @Override
    public Color getColorSummary() {
        return Color.GREEN;
    }

    private <T> void drawShape(final Graphics2D g, final Node<T> node, final EuclideanPhysics2DEnvironment<T> env, final double zoom, final int x, final int y) {
        final GeometricShape geometricShape; // = node.getShape();
        if (node.contains(VISION)) {
            geometricShape = env.getShapeFactory().circle(CAM_SHAPE_SIZE);
        } else {
            geometricShape = env.getShapeFactory().circle(OBJ_SHAPE_SIZE);
        }
        if (geometricShape instanceof AwtShapeCompatible) {
            final AffineTransform transform = getTransform(x, y, zoom, getRotation(node, env));
            final Shape shape = transform.createTransformedShape(((AwtShapeCompatible) geometricShape).asAwtShape());

            if (node.contains(WANTED)) {
                g.setColor(COLOR_WANTED);
            } else if(node.contains(VISION)) {
                g.setColor(COLOR_CAMERA);
            } else {
                g.setColor(COLOR_OBJECT);
            }
            g.fill(shape);
        }
    }

    private <T> void drawFieldOfView(final Graphics2D g, final Node<T> node, final EuclideanPhysics2DEnvironment<T> env, final double zoom, final int x, final int y) {
        final AffineTransform transform = getTransform(x, y, zoom, getRotation(node, env));
        g.setColor(COLOR_FOV);
        node.getReactions()
                .stream()
                .flatMap(r -> r.getActions().stream())
                .filter(a -> a instanceof See)
                .map(a -> (See) a)
                .forEach(a -> {
                    final double angle = a.getAngle();
                    final double startAngle = -angle / 2;
                    final double d = a.getDistance();
                    final Shape fov = new Arc2D.Double(-d, -d, d * 2, d * 2, startAngle, angle, Arc2D.PIE);
                    g.draw(transform.createTransformedShape(fov));
                });
    }

    private <T> double getRotation(final Node<T> node, final EuclideanPhysics2DEnvironment<T> env) {
        final Euclidean2DPosition direction = env.getHeading(node);
        return Math.atan2(direction.getY(), direction.getX());
    }

    private AffineTransform getTransform(final int x, final int y, final double zoom, final double rotation) {
        final AffineTransform transform = new AffineTransform();
        transform.translate(x, y);
        transform.scale(zoom, zoom);
        transform.rotate(-rotation); // invert angle because the y axis is inverted in the gui
        return transform;
    }
}