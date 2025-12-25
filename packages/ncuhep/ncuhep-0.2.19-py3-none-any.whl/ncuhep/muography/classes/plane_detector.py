from ...units import Length
import os
import json
import numpy as np


class PlaneDetector:
    def __init__(self):
        # pixel info
        self.pixel_footprint_length_x = Length()
        self.pixel_footprint_length_y = Length()
        self.pixel_footprint_length_z = Length()

        self.pixel_actual_length_x = Length()
        self.pixel_actual_length_y = Length()
        self.pixel_actual_length_z = Length()

        # board info
        self.channels_per_board_x = None
        self.channels_per_board_y = None

        self.channels_per_board = None

        # layer info
        self.boards_per_layer_x = None
        self.boards_per_layer_y = None

        self.boards_per_layer = None

        self.layer_z = Length()
        self.layer_id = None

        self.board_flip_x = None
        self.board_flip_y = None
        self.board_flip_z = None

        self.layer_flip_x = None
        self.layer_flip_y = None

        # sanity check - layer info
        self.layer_count = None
        self.pixel_count_per_layer_x = None
        self.pixel_count_per_layer_y = None

        self.pixel_count_per_layer = None

        self.board_counts = None
        # detector info
        self.detector_half_length_x = Length()
        self.detector_half_length_y = Length()

        # mapping info
        self.forward_mapping = None
        self.reverse_mapping = None

        self.layer_mapping = None

    def _import(self, path):
        config = json.load(open(path, "r"))

        self.pixel_footprint_length_x.mm = config["pixel_footprint_length_x_mm"]
        self.pixel_footprint_length_y.mm = config["pixel_footprint_length_y_mm"]
        self.pixel_footprint_length_z.mm = config["pixel_footprint_length_z_mm"]

        self.pixel_actual_length_x.mm = config["pixel_actual_length_x_mm"]
        self.pixel_actual_length_y.mm = config["pixel_actual_length_y_mm"]
        self.pixel_actual_length_z.mm = config["pixel_actual_length_z_mm"]

        self.channels_per_board_x = config["channels_per_board_x"]
        self.channels_per_board_y = config["channels_per_board_y"]
        self.channels_per_board = config["channels_per_board"]

        self.boards_per_layer_x = np.array(config["boards_per_layer_x"], dtype=np.int64)
        self.boards_per_layer_y = np.array(config["boards_per_layer_y"], dtype=np.int64)
        self.boards_per_layer = np.array(config["boards_per_layer"], dtype=np.int64)

        self.layer_z.mm = np.array(config["layer_z_mm"], dtype=np.float64)
        self.layer_id = np.array(config["layer_id"], dtype=np.int64)
        self.layer_count = config["layer_count"]

        self.board_counts = config["board_counts"]

        self.board_flip_x = np.array(config.get("board_flip_x", [0] * self.board_counts), dtype=np.int64)
        self.board_flip_y = np.array(config.get("board_flip_y", [0] * self.board_counts), dtype=np.int64)
        self.board_flip_z = config["board_flip_z"]

        self.layer_flip_x = np.array(config.get("layer_flip_x", [0] * self.layer_count), dtype=np.int64)
        self.layer_flip_y = np.array(config.get("layer_flip_y", [0] * self.layer_count), dtype=np.int64)

        self.pixel_count_per_layer_x = np.array(config["pixel_count_per_layer_x"], dtype=np.int64)
        self.pixel_count_per_layer_y = np.array(config["pixel_count_per_layer_y"], dtype=np.int64)
        self.pixel_count_per_layer = np.array(config["pixel_count_per_layer"], dtype=np.int64)

        self.detector_half_length_x.mm = np.array(config["detector_half_length_x_mm"], dtype=np.float64)
        self.detector_half_length_y.mm = np.array(config["detector_half_length_y_mm"], dtype=np.float64)

        self.create_mapping()

    def _export(self, path):
        config = {
            "pixel_footprint_length_x_mm": self.pixel_footprint_length_x.mm,
            "pixel_footprint_length_y_mm": self.pixel_footprint_length_y.mm,
            "pixel_footprint_length_z_mm": self.pixel_footprint_length_z.mm,
            "pixel_actual_length_x_mm": self.pixel_actual_length_x.mm,
            "pixel_actual_length_y_mm": self.pixel_actual_length_y.mm,
            "pixel_actual_length_z_mm": self.pixel_actual_length_z.mm,
            "channels_per_board_x": self.channels_per_board_x,
            "channels_per_board_y": self.channels_per_board_y,
            "channels_per_board": self.channels_per_board,
            "boards_per_layer_x": self.boards_per_layer_x.tolist(),
            "boards_per_layer_y": self.boards_per_layer_y.tolist(),
            "boards_per_layer": self.boards_per_layer.tolist(),
            "layer_z_mm": self.layer_z.mm.tolist(),
            "layer_id": self.layer_id.tolist(),
            "board_flip_x": self.board_flip_x.tolist() if self.board_flip_x is not None else [0] * self.board_counts,
            "board_flip_y": self.board_flip_y.tolist() if self.board_flip_y is not None else [0] * self.board_counts,
            "board_flip_z": self.board_flip_z if self.board_flip_z is not None else 0,
            "layer_flip_x": self.layer_flip_x.tolist() if self.layer_flip_x is not None else [0] * self.layer_count,
            "layer_flip_y": self.layer_flip_y.tolist() if self.layer_flip_y is not None else [0] * self.layer_count,
            "layer_count": self.layer_count,
            "pixel_count_per_layer_x": self.pixel_count_per_layer_x.tolist(),
            "pixel_count_per_layer_y": self.pixel_count_per_layer_y.tolist(),
            "pixel_count_per_layer": self.pixel_count_per_layer.tolist(),
            "board_counts": self.board_counts,
            "detector_half_length_x_mm": self.detector_half_length_x.mm.tolist(),
            "detector_half_length_y_mm": self.detector_half_length_y.mm.tolist()
        }

        assert "json" in os.path.splitext(path)[1], "File extension must be .json"

        json.dump(config, open(path, "w"), indent=4)

    def create_mapping(self):

        channel = np.arange(0, self.channels_per_board, 1)
        if self.board_flip_z:
            channel = channel[::-1]

        # Create initial mapping
        layers = []
        for i in range(self.layer_count):
            layers.append(np.tile(channel, self.boards_per_layer[i]).reshape(self.boards_per_layer[i], self.channels_per_board))

        layers = np.concatenate(layers, axis=0, dtype=np.int64)

        # Assign global channel IDs
        for boardID, board in enumerate(layers):
            for channelID, channel in enumerate(board):
                layers[boardID][channelID] = int((boardID * self.channels_per_board) + channel)

        layers_ = []
        val = 0
        for i in range(self.layer_count):
            layers_.append(layers[val:val + self.boards_per_layer[i]].reshape(self.boards_per_layer[i], self.channels_per_board_x, self.channels_per_board_y))
            val += self.boards_per_layer[i]

        val = 0
        for i in range(self.layer_count):
            for j in range(self.boards_per_layer[i]):
                if self.board_flip_x[val] == 1:
                    layers_[i][j] = np.flip(layers_[i][j], axis=1)
                if self.board_flip_y[val] == 1:
                    layers_[i][j] = np.flip(layers_[i][j], axis=0)
                val += 1

        layers = []
        for i, layer in enumerate(layers_):
            layer_ = layer.reshape(self.boards_per_layer_x[i], self.boards_per_layer_y[i], self.channels_per_board_x, self.channels_per_board_y)
            layer_ = np.transpose(layer_, (0, 2, 1, 3))
            layer_ = layer_.reshape(self.boards_per_layer[i], self.channels_per_board)

            layers.append(layer_)

        layers = np.concatenate(layers, axis=0, dtype=np.int64).reshape(-1)

        # layers = layers.reshape((self.layer_count, self.boards_per_layer_x * self.channels_per_board_x,
        #                         self.boards_per_layer_y * self.channels_per_board_y))

        layers_ = []

        for i in range(self.layer_count):
            layer_channels_x = self.boards_per_layer_x[i] * self.channels_per_board_x
            layer_channels_y = self.boards_per_layer_y[i] * self.channels_per_board_y
            layers_.append(layers[i * layer_channels_x * layer_channels_y:(i + 1) * layer_channels_x * layer_channels_y].reshape(layer_channels_x, layer_channels_y))

        for i in range(self.layer_count):
            if self.layer_flip_x[i] == 1:
                layers_[i] = np.flip(layers_[i], axis=1)
            if self.layer_flip_y[i] == 1:
                layers_[i] = np.flip(layers_[i], axis=0)

        layers = np.concatenate(layers_, axis=0, dtype=np.int64).reshape(-1)
        order = np.argsort(layers)

        self.forward_mapping = order.reshape(self.board_counts, self.channels_per_board)
        self.reverse_mapping = layers.reshape(self.board_counts, self.channels_per_board)

        self.layer_mapping = np.zeros(self.board_counts, dtype=np.int64)
        val = 0
        for i in range(self.layer_count):
            self.layer_mapping[val:val + self.boards_per_layer[i]] = self.layer_id[i]
            val += self.boards_per_layer[i]

        # plot mapping for verification
        import matplotlib.pyplot as plt

        n_to_plot = min(self.layer_count, 4)

        plt.rcParams.update({'font.family': 'monospace'})
        plt.rcParams.update({'font.size': 16})
        fig, axes = plt.subplots(2, 2, figsize=(10, 10), dpi=600)
        axes = axes.ravel()

        # ---- global color scale across all plotted layers ----
        vmin = np.min([layers_[i].min() for i in range(n_to_plot)])
        vmax = np.max([layers_[i].max() for i in range(n_to_plot)])

        last_im = None
        for i in range(n_to_plot):
            ax = axes[i]
            img = layers_[i]  # 2D array for this layer (any shape)

            # plot with shared vmin/vmax so colors are comparable
            last_im = ax.imshow(img, cmap='coolwarm', interpolation='nearest',
                                vmin=vmin, vmax=vmax)

            ny, nx = img.shape
            # annotate each cell with its value
            for x in range(ny):
                for y in range(nx):
                    ax.text(y, x, str(img[x, y]),
                            color='black', ha='center', va='center', fontsize=12)

            ax.set_title(f'Layer {self.layer_id[i]} Mapping')
            ax.set_xlabel('Channel X')
            ax.set_ylabel('Channel Y')
            ax.grid(False)

        # hide any unused subplots if you have < 4 layers
        for j in range(n_to_plot, 4):
            fig.delaxes(axes[j])

        fig.tight_layout()
        plt.savefig("detector_mapping_verification.png", dpi=600, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    detector_9449 = PlaneDetector()

    detector_9449.pixel_footprint_length_x.mm = 50
    detector_9449.pixel_footprint_length_y.mm = 50
    detector_9449.pixel_footprint_length_z.mm = 12

    detector_9449.pixel_actual_length_x.mm = 49
    detector_9449.pixel_actual_length_y.mm = 49
    detector_9449.pixel_actual_length_z.mm = 12

    detector_9449.channels_per_board_x = 4
    detector_9449.channels_per_board_y = 4
    detector_9449.channels_per_board = 16

    detector_9449.boards_per_layer_x = np.array([3, 2, 2, 3], dtype=np.int64)
    detector_9449.boards_per_layer_y = np.array([3, 2, 2, 3], dtype=np.int64)
    detector_9449.boards_per_layer = np.array([9, 4, 4, 9], dtype=np.int64)

    detector_9449.layer_z.mm = np.array([-750, -250, 250, 750], dtype=np.float64)
    detector_9449.layer_id = np.array([1, 2, 3, 4], dtype=np.int64)
    detector_9449.layer_count = 4

    detector_9449.board_flip_x = np.array([
        0, 1,
        0, 1,

        0, 1, 0,
        1, 0, 1,
        0, 0, 1,

        1, 0, 0,
        1, 0, 1,
        0, 1, 0,

        1, 0,
        1, 0], dtype=np.int64)

    detector_9449.board_flip_y = np.array([
        0, 0,
        0, 0,

        0, 0, 0,
        0, 0, 0,
        0, 0, 0,

        0, 0, 0,
        0, 0, 0,
        0, 0, 0,

        0, 0,
        0, 0], dtype=np.int64)

    detector_9449.layer_flip_x = np.array([0, 0, 0, 0], dtype=np.int64)
    detector_9449.layer_flip_y = np.array([0, 0, 0, 0], dtype=np.int64)

    detector_9449.pixel_count_per_layer_x = np.array([12, 8, 8, 12], dtype=np.int64)
    detector_9449.pixel_count_per_layer_y = np.array([12, 8, 8, 12], dtype=np.int64)
    detector_9449.pixel_count_per_layer = np.array([144, 64, 64, 144], dtype=np.int64)

    detector_9449.board_counts = 26

    detector_9449.detector_half_length_x.mm = np.array([300, 200, 200, 300], dtype=np.float64)
    detector_9449.detector_half_length_y.mm = np.array([300, 200, 200, 300], dtype=np.float64)

    detector_9449._import()

