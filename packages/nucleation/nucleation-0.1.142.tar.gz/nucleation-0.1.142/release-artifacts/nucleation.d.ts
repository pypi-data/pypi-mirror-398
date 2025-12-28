/* tslint:disable */
/* eslint-disable */

export class BlockPosition {
  free(): void;
  [Symbol.dispose](): void;
  constructor(x: number, y: number, z: number);
  x: number;
  y: number;
  z: number;
}

export class BlockStateWrapper {
  free(): void;
  [Symbol.dispose](): void;
  properties(): any;
  with_property(key: string, value: string): void;
  constructor(name: string);
  name(): string;
}

export class BrushWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create a point cloud gradient brush using Inverse Distance Weighting (IDW)
   * positions: Flat array [x1, y1, z1, x2, y2, z2, ...]
   * colors: Flat array [r1, g1, b1, r2, g2, b2, ...]
   * falloff: Power parameter (default 2.0 if None)
   */
  static point_gradient(positions: Int32Array, colors: Uint8Array, falloff?: number | null, space?: number | null, palette_filter?: string[] | null): BrushWrapper;
  /**
   * Create a linear gradient brush
   * Space: 0 = RGB, 1 = Oklab
   */
  static linear_gradient(x1: number, y1: number, z1: number, r1: number, g1: number, b1: number, x2: number, y2: number, z2: number, r2: number, g2: number, b2: number, space?: number | null, palette_filter?: string[] | null): BrushWrapper;
  /**
   * Create a color brush (matches closest block to RGB color)
   * Palette: optional list of block IDs to restrict matching to.
   */
  static color(r: number, g: number, b: number, palette_filter?: string[] | null): BrushWrapper;
  /**
   * Create a solid brush with a specific block
   */
  static solid(block_state: string): BrushWrapper;
  /**
   * Create a shaded brush (Lambertian shading)
   * light_dir: [x, y, z] vector
   */
  static shaded(r: number, g: number, b: number, lx: number, ly: number, lz: number, palette_filter?: string[] | null): BrushWrapper;
}

export class CircuitBuilderWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Add an input with full control
   *
   * Uses the default sort strategy (YXZ - Y first, then X, then Z).
   * For custom ordering, use `withInputSorted`.
   */
  withInput(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper): CircuitBuilderWrapper;
  /**
   * Create a CircuitBuilder pre-populated from Insign annotations
   */
  static fromInsign(schematic: SchematicWrapper): CircuitBuilderWrapper;
  /**
   * Get the current number of inputs
   */
  inputCount(): number;
  /**
   * Get the names of defined inputs
   */
  inputNames(): string[];
  /**
   * Add an output with full control
   *
   * Uses the default sort strategy (YXZ - Y first, then X, then Z).
   * For custom ordering, use `withOutputSorted`.
   */
  withOutput(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper): CircuitBuilderWrapper;
  /**
   * Get the current number of outputs
   */
  outputCount(): number;
  /**
   * Get the names of defined outputs
   */
  outputNames(): string[];
  /**
   * Set simulation options
   */
  withOptions(options: SimulationOptionsWrapper): CircuitBuilderWrapper;
  /**
   * Build with validation (convenience method)
   */
  buildValidated(): TypedCircuitExecutorWrapper;
  /**
   * Add an input with automatic layout inference
   *
   * Uses the default sort strategy (YXZ - Y first, then X, then Z).
   * For custom ordering, use `withInputAutoSorted`.
   */
  withInputAuto(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper): CircuitBuilderWrapper;
  /**
   * Set state mode: 'stateless', 'stateful', or 'manual'
   */
  withStateMode(mode: string): CircuitBuilderWrapper;
  /**
   * Add an output with automatic layout inference
   *
   * Uses the default sort strategy (YXZ - Y first, then X, then Z).
   * For custom ordering, use `withOutputAutoSorted`.
   */
  withOutputAuto(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper): CircuitBuilderWrapper;
  /**
   * Add an input with full control and custom sort strategy
   */
  withInputSorted(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper, sort: SortStrategyWrapper): CircuitBuilderWrapper;
  /**
   * Add an output with full control and custom sort strategy
   */
  withOutputSorted(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper, sort: SortStrategyWrapper): CircuitBuilderWrapper;
  /**
   * Add an input with automatic layout inference and custom sort strategy
   */
  withInputAutoSorted(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper, sort: SortStrategyWrapper): CircuitBuilderWrapper;
  /**
   * Add an output with automatic layout inference and custom sort strategy
   */
  withOutputAutoSorted(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper, sort: SortStrategyWrapper): CircuitBuilderWrapper;
  /**
   * Create a new CircuitBuilder from a schematic
   */
  constructor(schematic: SchematicWrapper);
  /**
   * Build the TypedCircuitExecutor
   */
  build(): TypedCircuitExecutorWrapper;
  /**
   * Validate the circuit configuration
   */
  validate(): void;
}

export class DefinitionRegionWrapper {
  free(): void;
  [Symbol.dispose](): void;
  addBounds(min: any, max: any): DefinitionRegionWrapper;
  addFilter(filter: string): DefinitionRegionWrapper;
  /**
   * Get the center point of the region as f32 (for rendering)
   *
   * Returns [x, y, z] as floats or null if empty
   */
  centerF32(): any;
  /**
   * Create a new region contracted by the given amount (immutable)
   */
  contracted(amount: number): DefinitionRegionWrapper;
  /**
   * Get the dimensions (width, height, length) of the overall bounding box
   *
   * Returns [width, height, length] or [0, 0, 0] if empty
   */
  dimensions(): Array<any>;
  getBlocks(): Array<any>;
  /**
   * Get the overall bounding box encompassing all boxes in this region
   * Returns an object with {min: [x,y,z], max: [x,y,z]} or null if empty
   */
  getBounds(): any;
  /**
   * Create a new region with points from `other` removed (immutable)
   */
  subtracted(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  /**
   * Add all points from another region to this one (mutating union)
   */
  unionInto(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  static fromBounds(min: BlockPosition, max: BlockPosition): DefinitionRegionWrapper;
  /**
   * Create a new region with only points in both (immutable)
   */
  intersected(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  /**
   * Clone this region (alias for copy)
   */
  clone(): DefinitionRegionWrapper;
  /**
   * Get a metadata value by key
   *
   * Returns the value string or null if not found
   */
  getMetadata(key: string): any;
  setMetadata(key: string, value: string): DefinitionRegionWrapper;
  excludeBlock(block_name: string): DefinitionRegionWrapper;
  /**
   * Check if all points in the region are connected (6-connectivity)
   */
  isContiguous(): boolean;
  /**
   * Get all metadata keys
   */
  metadataKeys(): Array<any>;
  /**
   * Create a DefinitionRegion from an array of positions
   *
   * Takes an array of [x, y, z] arrays. Adjacent points will be merged into boxes.
   */
  static fromPositions(positions: any): DefinitionRegionWrapper;
  filterByBlock(schematic: SchematicWrapper, block_name: string): DefinitionRegionWrapper;
  /**
   * Get all metadata as a JS object
   */
  getAllMetadata(): any;
  /**
   * Get positions in globally sorted order (Y, then X, then Z)
   *
   * This provides **deterministic bit ordering** for circuits regardless of
   * how the region was constructed. Use this for IO bit assignment.
   */
  positionsSorted(): Array<any>;
  /**
   * Check if this region intersects with a bounding box
   *
   * Useful for frustum culling in renderers.
   */
  intersectsBounds(min_x: number, min_y: number, min_z: number, max_x: number, max_y: number, max_z: number): boolean;
  /**
   * Create a DefinitionRegion from multiple bounding boxes
   *
   * Takes an array of {min: [x,y,z], max: [x,y,z]} objects.
   * Unlike fromPositions which merges adjacent points, this keeps boxes as provided.
   */
  static fromBoundingBoxes(boxes: any): DefinitionRegionWrapper;
  /**
   * Get the number of connected components in this region
   */
  connectedComponents(): number;
  /**
   * Filter positions by block state properties (JS object)
   * Only keeps positions where the block has ALL specified properties matching
   */
  filterByProperties(schematic: SchematicWrapper, properties: any): DefinitionRegionWrapper;
  constructor();
  /**
   * Create a deep copy of this region
   */
  copy(): DefinitionRegionWrapper;
  merge(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  /**
   * Translate all boxes by the given offset
   */
  shift(x: number, y: number, z: number): DefinitionRegionWrapper;
  /**
   * Create a new region that is the union of this region and another
   */
  union(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  /**
   * Get the center point of the region (integer coordinates)
   *
   * Returns [x, y, z] or null if empty
   */
  center(): any;
  /**
   * Expand all boxes by the given amounts in each direction
   */
  expand(x: number, y: number, z: number): DefinitionRegionWrapper;
  /**
   * Get total volume (number of blocks) covered by all boxes
   */
  volume(): number;
  /**
   * Get a specific bounding box by index
   *
   * Returns {min: [x,y,z], max: [x,y,z]} or null if index is out of bounds
   */
  getBox(index: number): any;
  /**
   * Create a new region shifted by the given offset (immutable)
   */
  shifted(x: number, y: number, z: number): DefinitionRegionWrapper;
  /**
   * Check if the region contains a specific point
   */
  contains(x: number, y: number, z: number): boolean;
  /**
   * Contract all boxes by the given amount uniformly
   */
  contract(amount: number): DefinitionRegionWrapper;
  /**
   * Create a new region expanded by the given amounts (immutable)
   */
  expanded(x: number, y: number, z: number): DefinitionRegionWrapper;
  /**
   * Check if the region is empty
   */
  isEmpty(): boolean;
  /**
   * Simplify the region by merging adjacent/overlapping boxes
   */
  simplify(): DefinitionRegionWrapper;
  /**
   * Subtract another region from this one (removes points present in `other`)
   */
  subtract(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  addPoint(x: number, y: number, z: number): DefinitionRegionWrapper;
  /**
   * Get the number of bounding boxes in this region
   */
  boxCount(): number;
  /**
   * Get all bounding boxes in this region
   *
   * Returns an array of {min: [x,y,z], max: [x,y,z]} objects.
   * Useful for rendering each box separately.
   */
  getBoxes(): Array<any>;
  /**
   * Keep only points present in both regions (intersection)
   */
  intersect(other: DefinitionRegionWrapper): DefinitionRegionWrapper;
  /**
   * Get a list of all positions as an array of [x, y, z] arrays
   */
  positions(): Array<any>;
  setColor(color: number): DefinitionRegionWrapper;
}

export class ExecutionModeWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Run for a fixed number of ticks
   */
  static fixedTicks(ticks: number): ExecutionModeWrapper;
  /**
   * Run until any output changes
   */
  static untilChange(max_ticks: number, check_interval: number): ExecutionModeWrapper;
  /**
   * Run until outputs are stable
   */
  static untilStable(stable_ticks: number, max_ticks: number): ExecutionModeWrapper;
  /**
   * Run until an output meets a condition
   */
  static untilCondition(output_name: string, condition: OutputConditionWrapper, max_ticks: number, check_interval: number): ExecutionModeWrapper;
}

export class IoLayoutBuilderWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Add an output
   */
  addOutput(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, positions: any[]): IoLayoutBuilderWrapper;
  /**
   * Add an input with automatic layout inference
   */
  addInputAuto(name: string, io_type: IoTypeWrapper, positions: any[]): IoLayoutBuilderWrapper;
  /**
   * Add an output with automatic layout inference
   */
  addOutputAuto(name: string, io_type: IoTypeWrapper, positions: any[]): IoLayoutBuilderWrapper;
  /**
   * Add an input defined by a region (bounding box)
   * Iterates Y (layers), then X (rows), then Z (columns)
   */
  addInputRegion(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, min: BlockPosition, max: BlockPosition): IoLayoutBuilderWrapper;
  /**
   * Add an output defined by a region (bounding box)
   * Iterates Y (layers), then X (rows), then Z (columns)
   */
  addOutputRegion(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, min: BlockPosition, max: BlockPosition): IoLayoutBuilderWrapper;
  /**
   * Add an input defined by a DefinitionRegion
   */
  addInputFromRegion(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper): IoLayoutBuilderWrapper;
  /**
   * Add an input defined by a region with automatic layout inference
   */
  addInputRegionAuto(name: string, io_type: IoTypeWrapper, min: BlockPosition, max: BlockPosition): IoLayoutBuilderWrapper;
  /**
   * Add an output defined by a DefinitionRegion
   */
  addOutputFromRegion(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, region: DefinitionRegionWrapper): IoLayoutBuilderWrapper;
  /**
   * Add an output defined by a region with automatic layout inference
   */
  addOutputRegionAuto(name: string, io_type: IoTypeWrapper, min: BlockPosition, max: BlockPosition): IoLayoutBuilderWrapper;
  /**
   * Add an input defined by a DefinitionRegion with automatic layout inference
   */
  addInputFromRegionAuto(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper): IoLayoutBuilderWrapper;
  /**
   * Add an output defined by a DefinitionRegion with automatic layout inference
   */
  addOutputFromRegionAuto(name: string, io_type: IoTypeWrapper, region: DefinitionRegionWrapper): IoLayoutBuilderWrapper;
  /**
   * Create a new IO layout builder
   */
  constructor();
  /**
   * Build the IO layout
   */
  build(): IoLayoutWrapper;
  /**
   * Add an input
   */
  addInput(name: string, io_type: IoTypeWrapper, layout: LayoutFunctionWrapper, positions: any[]): IoLayoutBuilderWrapper;
}

export class IoLayoutWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Get input names
   */
  inputNames(): string[];
  /**
   * Get output names
   */
  outputNames(): string[];
}

export class IoTypeWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create a signed integer type
   */
  static signedInt(bits: number): IoTypeWrapper;
  /**
   * Create an unsigned integer type
   */
  static unsignedInt(bits: number): IoTypeWrapper;
  /**
   * Create an ASCII string type
   */
  static ascii(chars: number): IoTypeWrapper;
  /**
   * Create a Boolean type
   */
  static boolean(): IoTypeWrapper;
  /**
   * Create a Float32 type
   */
  static float32(): IoTypeWrapper;
}

export class LayoutFunctionWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * One bit per position (0 or 15)
   */
  static oneToOne(): LayoutFunctionWrapper;
  /**
   * Column-major 2D layout
   */
  static columnMajor(rows: number, cols: number, bits_per_element: number): LayoutFunctionWrapper;
  /**
   * Custom bit-to-position mapping
   */
  static custom(mapping: Uint32Array): LayoutFunctionWrapper;
  /**
   * Four bits per position (0-15)
   */
  static packed4(): LayoutFunctionWrapper;
  /**
   * Scanline layout for screens
   */
  static scanline(width: number, height: number, bits_per_pixel: number): LayoutFunctionWrapper;
  /**
   * Row-major 2D layout
   */
  static rowMajor(rows: number, cols: number, bits_per_element: number): LayoutFunctionWrapper;
}

export class LazyChunkIterator {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  total_chunks(): number;
  current_position(): number;
  /**
   * Get the next chunk on-demand (generates it fresh, doesn't store it)
   */
  next(): any;
  reset(): void;
  skip_to(index: number): void;
  has_next(): boolean;
}

export class MchprsWorldWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Simulates a right-click on a block (typically a lever)
   */
  on_use_block(x: number, y: number, z: number): void;
  /**
   * Creates a simulation world with custom options
   */
  static with_options(schematic: SchematicWrapper, options: SimulationOptionsWrapper): MchprsWorldWrapper;
  /**
   * Gets a copy of the underlying schematic
   *
   * Note: Call sync_to_schematic() first if you want the latest simulation state
   */
  get_schematic(): SchematicWrapper;
  /**
   * Consumes the simulation world and returns the schematic with simulation state
   *
   * This automatically syncs before returning
   */
  into_schematic(): SchematicWrapper;
  /**
   * Gets the power state of a lever
   */
  get_lever_power(x: number, y: number, z: number): boolean;
  /**
   * Generates a truth table for the circuit
   *
   * Returns an array of objects with keys like "Input 0", "Output 0", etc.
   */
  get_truth_table(): any;
  /**
   * Syncs the current simulation state back to the underlying schematic
   *
   * Call this after running simulation to update block states (redstone power, lever states, etc.)
   */
  sync_to_schematic(): void;
  /**
   * Gets the redstone power level at a position
   */
  get_redstone_power(x: number, y: number, z: number): number;
  /**
   * Gets the signal strength at a specific block position (for custom IO nodes)
   */
  getSignalStrength(x: number, y: number, z: number): number;
  /**
   * Sets the signal strength at a specific block position (for custom IO nodes)
   */
  setSignalStrength(x: number, y: number, z: number, strength: number): void;
  /**
   * Get custom IO changes without clearing the queue
   */
  peekCustomIoChanges(): any;
  /**
   * Get and clear all custom IO changes since last poll
   * Returns an array of change objects with {x, y, z, oldPower, newPower}
   */
  pollCustomIoChanges(): any;
  /**
   * Check for custom IO state changes and queue them
   * Call this after tick() or setSignalStrength() to detect changes
   */
  checkCustomIoChanges(): void;
  /**
   * Clear all queued custom IO changes
   */
  clearCustomIoChanges(): void;
  constructor(schematic: SchematicWrapper);
  /**
   * Advances the simulation by the specified number of ticks
   */
  tick(number_of_ticks: number): void;
  /**
   * Flushes pending changes from the compiler to the world
   */
  flush(): void;
  /**
   * Checks if a redstone lamp is lit at the given position
   */
  is_lit(x: number, y: number, z: number): boolean;
}

export class OutputConditionWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Output not equals a value
   */
  static notEquals(value: ValueWrapper): OutputConditionWrapper;
  /**
   * Bitwise AND with mask
   */
  static bitwiseAnd(mask: number): OutputConditionWrapper;
  /**
   * Output greater than a value
   */
  static greaterThan(value: ValueWrapper): OutputConditionWrapper;
  /**
   * Output equals a value
   */
  static equals(value: ValueWrapper): OutputConditionWrapper;
  /**
   * Output less than a value
   */
  static lessThan(value: ValueWrapper): OutputConditionWrapper;
}

export class PaletteManager {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Get all wool blocks
   */
  static getWoolBlocks(): string[];
  /**
   * Get all concrete blocks
   */
  static getConcreteBlocks(): string[];
  /**
   * Get all terracotta blocks
   */
  static getTerracottaBlocks(): string[];
  /**
   * Get a palette containing blocks matching ANY of the provided keywords
   * Example: `["wool", "obsidian"]` gets all wool blocks AND obsidian
   */
  static getPaletteByKeywords(keywords: string[]): string[];
}

export class SchematicBuilderWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create from template string
   */
  static fromTemplate(template: string): SchematicBuilderWrapper;
  /**
   * Map a character to a block string
   */
  map(ch: string, block: string): SchematicBuilderWrapper;
  /**
   * Create a new schematic builder with standard palette
   */
  constructor();
  /**
   * Set the name of the schematic
   */
  name(name: string): SchematicBuilderWrapper;
  /**
   * Build the schematic
   */
  build(): SchematicWrapper;
}

export class SchematicWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Creates a simulation world for this schematic with default options
   *
   * This allows you to simulate redstone circuits and interact with them.
   */
  create_simulation_world(): MchprsWorldWrapper;
  /**
   * Creates a simulation world for this schematic with custom options
   *
   * This allows you to configure simulation behavior like wire state tracking.
   */
  create_simulation_world_with_options(options: SimulationOptionsWrapper): MchprsWorldWrapper;
  debug_info(): string;
  get_volume(): number;
  copy_region(from_schematic: SchematicWrapper, min_x: number, min_y: number, min_z: number, max_x: number, max_y: number, max_z: number, target_x: number, target_y: number, target_z: number, excluded_blocks: any): void;
  fillCuboid(min_x: number, min_y: number, min_z: number, max_x: number, max_y: number, max_z: number, block_state: string): void;
  fillSphere(cx: number, cy: number, cz: number, radius: number, block_state: string): void;
  get_palette(): any;
  to_litematic(): Uint8Array;
  to_schematic(): Uint8Array;
  createRegion(name: string, min: any, max: any): DefinitionRegionWrapper;
  /**
   * Extract all sign text from the schematic
   * Returns a JavaScript array of objects: [{pos: [x,y,z], text: "..."}]
   */
  extractSigns(): any;
  /**
   * Flip a specific region along the X axis
   */
  flip_region_x(region_name: string): void;
  /**
   * Flip a specific region along the Y axis
   */
  flip_region_y(region_name: string): void;
  /**
   * Flip a specific region along the Z axis
   */
  flip_region_z(region_name: string): void;
  updateRegion(name: string, region: DefinitionRegionWrapper): void;
  /**
   * All blocks as palette indices - for when you need everything at once but efficiently
   * Returns array of [x, y, z, palette_index]
   */
  blocks_indices(): Array<any>;
  buildExecutor(config: any): TypedCircuitExecutorWrapper;
  /**
   * Optimized chunks iterator that returns palette indices instead of full block data
   * Returns array of: { chunk_x, chunk_y, chunk_z, blocks: [[x,y,z,palette_index],...] }
   */
  chunks_indices(chunk_width: number, chunk_height: number, chunk_length: number): Array<any>;
  /**
   * Compile Insign annotations from the schematic's signs
   * Returns a JavaScript object with compiled region metadata
   * This returns raw Insign data - interpretation is up to the consumer
   */
  compileInsign(): any;
  createCircuit(inputs: any, outputs: any): TypedCircuitExecutorWrapper;
  from_litematic(data: Uint8Array): void;
  from_schematic(data: Uint8Array): void;
  /**
   * Get optimized chunk data including blocks and relevant tile entities
   * Returns { blocks: [[x,y,z,palette_index],...], entities: [{id, position, nbt},...] }
   */
  getChunkData(chunk_x: number, chunk_y: number, chunk_z: number, chunk_width: number, chunk_height: number, chunk_length: number): any;
  get_dimensions(): Int32Array;
  get_block_count(): number;
  print_schematic(): string;
  /**
   * Rotate a specific region around the X axis
   */
  rotate_region_x(region_name: string, degrees: number): void;
  /**
   * Rotate a specific region around the Y axis
   */
  rotate_region_y(region_name: string, degrees: number): void;
  /**
   * Rotate a specific region around the Z axis
   */
  rotate_region_z(region_name: string, degrees: number): void;
  /**
   * Get all palettes once - eliminates repeated string transfers
   * Returns: { default: [BlockState], regions: { regionName: [BlockState] } }
   */
  get_all_palettes(): any;
  get_block_entity(x: number, y: number, z: number): any;
  /**
   * Get block as formatted string with properties (e.g., "minecraft:lever[powered=true,facing=north]")
   */
  get_block_string(x: number, y: number, z: number): string | undefined;
  get_bounding_box(): any;
  get_chunk_blocks(offset_x: number, offset_y: number, offset_z: number, width: number, height: number, length: number): Array<any>;
  get_region_names(): string[];
  setBlockWithNbt(x: number, y: number, z: number, block_name: string, nbt_data: any): void;
  static get_format_versions(format: string): Array<any>;
  chunks_with_strategy(chunk_width: number, chunk_height: number, chunk_length: number, strategy: string, camera_x: number, camera_y: number, camera_z: number): Array<any>;
  /**
   * Get the tight bounding box max coordinates [x, y, z]
   * Returns null if no non-air blocks have been placed
   */
  get_tight_bounds_max(): Int32Array | undefined;
  /**
   * Get the tight bounding box min coordinates [x, y, z]
   * Returns null if no non-air blocks have been placed
   */
  get_tight_bounds_min(): Int32Array | undefined;
  /**
   * Get the tight dimensions of actual block content (excluding pre-allocated space)
   * Returns [width, height, length] or [0, 0, 0] if no non-air blocks exist
   */
  get_tight_dimensions(): Int32Array;
  to_schematic_version(version: string): Uint8Array;
  addDefinitionRegion(name: string, region: DefinitionRegionWrapper): void;
  getDefinitionRegion(name: string): DefinitionRegionWrapper;
  /**
   * Get optimization stats
   */
  get_optimization_info(): any;
  createCircuitBuilder(): CircuitBuilderWrapper;
  get_all_block_entities(): any;
  definitionRegionShift(name: string, x: number, y: number, z: number): void;
  get_palette_from_region(region_name: string): any;
  get_region_bounding_box(region_name: string): any;
  createDefinitionRegion(name: string): void;
  /**
   * Get the allocated dimensions (full buffer size including pre-allocated space)
   * Use this if you need to know the internal buffer size
   */
  get_allocated_dimensions(): Int32Array;
  /**
   * Get specific chunk blocks as palette indices (for lazy loading individual chunks)
   * Returns array of [x, y, z, palette_index]
   */
  get_chunk_blocks_indices(offset_x: number, offset_y: number, offset_z: number, width: number, height: number, length: number): Array<any>;
  removeDefinitionRegion(name: string): boolean;
  get_block_with_properties(x: number, y: number, z: number): BlockStateWrapper | undefined;
  set_block_with_properties(x: number, y: number, z: number, block_name: string, properties: any): void;
  create_lazy_chunk_iterator(chunk_width: number, chunk_height: number, chunk_length: number, strategy: string, camera_x: number, camera_y: number, camera_z: number): LazyChunkIterator;
  static get_default_format_version(format: string): string | undefined;
  get_default_region_palette(): any;
  definitionRegionAddPoint(name: string, x: number, y: number, z: number): void;
  getDefinitionRegionNames(): Array<any>;
  /**
   * Optimized chunks with strategy - returns palette indices
   */
  chunks_indices_with_strategy(chunk_width: number, chunk_height: number, chunk_length: number, strategy: string, camera_x: number, camera_y: number, camera_z: number): Array<any>;
  definitionRegionAddBounds(name: string, min: BlockPosition, max: BlockPosition): void;
  static get_supported_export_formats(): Array<any>;
  static get_supported_import_formats(): Array<any>;
  definitionRegionSetMetadata(name: string, key: string, value: string): void;
  get_available_schematic_versions(): Array<any>;
  createDefinitionRegionFromPoint(name: string, x: number, y: number, z: number): void;
  createDefinitionRegionFromBounds(name: string, min: BlockPosition, max: BlockPosition): void;
  constructor();
  blocks(): Array<any>;
  chunks(chunk_width: number, chunk_height: number, chunk_length: number): Array<any>;
  /**
   * Flip the schematic along the X axis
   */
  flip_x(): void;
  /**
   * Flip the schematic along the Y axis
   */
  flip_y(): void;
  /**
   * Flip the schematic along the Z axis
   */
  flip_z(): void;
  save_as(format: string, version?: string | null): Uint8Array;
  /**
   * Rotate the schematic around the X axis
   * Degrees must be 90, 180, or 270
   */
  rotate_x(degrees: number): void;
  /**
   * Rotate the schematic around the Y axis (horizontal plane)
   * Degrees must be 90, 180, or 270
   */
  rotate_y(degrees: number): void;
  /**
   * Rotate the schematic around the Z axis
   * Degrees must be 90, 180, or 270
   */
  rotate_z(degrees: number): void;
  from_data(data: Uint8Array): void;
  get_block(x: number, y: number, z: number): string | undefined;
  set_block(x: number, y: number, z: number, block_name: string): void;
}

export class ShapeWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create a new Cuboid shape
   */
  static cuboid(min_x: number, min_y: number, min_z: number, max_x: number, max_y: number, max_z: number): ShapeWrapper;
  /**
   * Create a new Sphere shape
   */
  static sphere(cx: number, cy: number, cz: number, radius: number): ShapeWrapper;
}

export class SimulationOptionsWrapper {
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Adds a position to the custom IO list
   */
  addCustomIo(x: number, y: number, z: number): void;
  /**
   * Clears the custom IO list
   */
  clearCustomIo(): void;
  constructor();
  io_only: boolean;
  optimize: boolean;
}

export class SortStrategyWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Sort by Y descending, then X descending, then Z descending
   */
  static descending(): SortStrategyWrapper;
  /**
   * Parse sort strategy from string
   *
   * Accepts: "yxz", "xyz", "zyx", "y_desc", "x_desc", "z_desc",
   *          "descending", "preserve", "reverse"
   */
  static fromString(s: string): SortStrategyWrapper;
  /**
   * Sort by Euclidean distance from a reference point (ascending)
   * Closest positions first. Useful for radial layouts.
   */
  static distanceFrom(x: number, y: number, z: number): SortStrategyWrapper;
  /**
   * Sort by Euclidean distance from a reference point (descending)
   * Farthest positions first.
   */
  static distanceFromDesc(x: number, y: number, z: number): SortStrategyWrapper;
  /**
   * Sort by X first (ascending), then Y, then Z
   */
  static xyz(): SortStrategyWrapper;
  /**
   * Sort by Y first (ascending), then X, then Z
   * Standard Minecraft layer-based ordering. This is the default.
   */
  static yxz(): SortStrategyWrapper;
  /**
   * Sort by Z first (ascending), then Y, then X
   */
  static zyx(): SortStrategyWrapper;
  /**
   * Reverse of whatever order positions were added
   */
  static reverse(): SortStrategyWrapper;
  /**
   * Preserve the order positions were added (no sorting)
   * Useful when you've manually ordered positions or are using `fromBoundingBoxes`
   * where box order matters.
   */
  static preserve(): SortStrategyWrapper;
  /**
   * Sort by X first (descending), then Y ascending, then Z ascending
   */
  static xDescYZ(): SortStrategyWrapper;
  /**
   * Sort by Y first (descending), then X ascending, then Z ascending
   */
  static yDescXZ(): SortStrategyWrapper;
  /**
   * Sort by Z first (descending), then Y ascending, then X ascending
   */
  static zDescYX(): SortStrategyWrapper;
  /**
   * Get the name of this strategy
   */
  readonly name: string;
}

export class StateModeConstants {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Manual state control
   */
  static readonly MANUAL: string;
  /**
   * Preserve state between executions
   */
  static readonly STATEFUL: string;
  /**
   * Always reset before execution (default)
   */
  static readonly STATELESS: string;
}

export class TypedCircuitExecutorWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create executor from Insign annotations in schematic
   */
  static fromInsign(schematic: SchematicWrapper): TypedCircuitExecutorWrapper;
  /**
   * Create executor from world and layout
   */
  static fromLayout(world: MchprsWorldWrapper, layout: IoLayoutWrapper): TypedCircuitExecutorWrapper;
  /**
   * Get all input names
   */
  inputNames(): string[];
  /**
   * Read a single output value without executing
   */
  readOutput(name: string): ValueWrapper;
  /**
   * Get all output names
   */
  outputNames(): string[];
  /**
   * Set state mode
   */
  setStateMode(mode: string): void;
  /**
   * Get detailed layout information for debugging and visualization
   *
   * Returns a JS object with the structure:
   * ```javascript
   * {
   *   inputs: {
   *     "name": {
   *       ioType: "UnsignedInt { bits: 8 }",
   *       positions: [[x, y, z], ...],  // In bit order (LSB first)
   *       bitCount: 8
   *     }
   *   },
   *   outputs: { ... }
   * }
   * ```
   */
  getLayoutInfo(): any;
  /**
   * Sync the simulation state back to the schematic
   *
   * Call this after execute() to update the schematic with the current simulation state.
   * Returns the updated schematic.
   */
  syncToSchematic(): SchematicWrapper;
  /**
   * Create executor from Insign annotations with custom simulation options
   */
  static fromInsignWithOptions(schematic: SchematicWrapper, options: SimulationOptionsWrapper): TypedCircuitExecutorWrapper;
  /**
   * Create executor from world, layout, and options
   */
  static fromLayoutWithOptions(world: MchprsWorldWrapper, layout: IoLayoutWrapper, options: SimulationOptionsWrapper): TypedCircuitExecutorWrapper;
  /**
   * Run the circuit with simplified arguments
   */
  run(inputs: any, limit: number, mode: string): any;
  /**
   * Manually advance the simulation by a specified number of ticks
   *
   * This is useful for manual state control when using 'manual' state mode.
   * Unlike execute(), this does not set any inputs or read outputs.
   */
  tick(ticks: number): void;
  /**
   * Manually flush the simulation state
   *
   * Ensures all pending changes are propagated through the redstone network.
   */
  flush(): void;
  /**
   * Reset the simulation
   */
  reset(): void;
  /**
   * Execute the circuit
   */
  execute(inputs: any, mode: ExecutionModeWrapper): any;
  /**
   * Set a single input value without executing
   */
  setInput(name: string, value: ValueWrapper): void;
}

export class ValueWrapper {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Create a String value
   */
  static fromString(value: string): ValueWrapper;
  /**
   * Convert to JavaScript value
   */
  toJs(): any;
  /**
   * Create an F32 value
   */
  static fromF32(value: number): ValueWrapper;
  /**
   * Create an I32 value
   */
  static fromI32(value: number): ValueWrapper;
  /**
   * Create a U32 value
   */
  static fromU32(value: number): ValueWrapper;
  /**
   * Create a Bool value
   */
  static fromBool(value: boolean): ValueWrapper;
  /**
   * Get type name
   */
  typeName(): string;
}

export class WasmBuildingTool {
  private constructor();
  free(): void;
  [Symbol.dispose](): void;
  /**
   * Apply a brush to a shape on the given schematic
   */
  static fill(schematic: SchematicWrapper, shape: ShapeWrapper, brush: BrushWrapper): void;
}

export function debug_json_schematic(schematic: SchematicWrapper): string;

export function debug_schematic(schematic: SchematicWrapper): string;

export function generate_gradient_between_blocks(start_block_id: string, end_block_id: string, steps: number, color_space: string, easing: string): any;

export function generate_gradient_between_colors(start_r: number, start_g: number, start_b: number, end_r: number, end_g: number, end_b: number, steps: number, color_space: string, easing: string): any;

export function get_all_colored_blocks(): any;

export function get_block_info(block_id: string): any;

export function get_color_spaces(): any;

export function get_easing_functions(): any;

export function sort_blocks_by_color_gradient(block_ids: string[]): any;

/**
 * Initialize WASM module with panic hook for better error messages
 */
export function start(): void;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
  readonly memory: WebAssembly.Memory;
  readonly __wbg_circuitbuilderwrapper_free: (a: number, b: number) => void;
  readonly __wbg_definitionregionwrapper_free: (a: number, b: number) => void;
  readonly __wbg_executionmodewrapper_free: (a: number, b: number) => void;
  readonly __wbg_iolayoutbuilderwrapper_free: (a: number, b: number) => void;
  readonly __wbg_iolayoutwrapper_free: (a: number, b: number) => void;
  readonly __wbg_iotypewrapper_free: (a: number, b: number) => void;
  readonly __wbg_layoutfunctionwrapper_free: (a: number, b: number) => void;
  readonly __wbg_mchprsworldwrapper_free: (a: number, b: number) => void;
  readonly __wbg_outputconditionwrapper_free: (a: number, b: number) => void;
  readonly __wbg_schematicbuilderwrapper_free: (a: number, b: number) => void;
  readonly __wbg_simulationoptionswrapper_free: (a: number, b: number) => void;
  readonly __wbg_sortstrategywrapper_free: (a: number, b: number) => void;
  readonly __wbg_statemodeconstants_free: (a: number, b: number) => void;
  readonly __wbg_typedcircuitexecutorwrapper_free: (a: number, b: number) => void;
  readonly __wbg_valuewrapper_free: (a: number, b: number) => void;
  readonly circuitbuilderwrapper_build: (a: number) => [number, number, number];
  readonly circuitbuilderwrapper_buildValidated: (a: number) => [number, number, number];
  readonly circuitbuilderwrapper_fromInsign: (a: number) => [number, number, number];
  readonly circuitbuilderwrapper_inputCount: (a: number) => number;
  readonly circuitbuilderwrapper_inputNames: (a: number) => [number, number];
  readonly circuitbuilderwrapper_new: (a: number) => number;
  readonly circuitbuilderwrapper_outputCount: (a: number) => number;
  readonly circuitbuilderwrapper_outputNames: (a: number) => [number, number];
  readonly circuitbuilderwrapper_validate: (a: number) => [number, number];
  readonly circuitbuilderwrapper_withInput: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly circuitbuilderwrapper_withInputAuto: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
  readonly circuitbuilderwrapper_withInputAutoSorted: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly circuitbuilderwrapper_withInputSorted: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly circuitbuilderwrapper_withOptions: (a: number, b: number) => number;
  readonly circuitbuilderwrapper_withOutput: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly circuitbuilderwrapper_withOutputAuto: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
  readonly circuitbuilderwrapper_withOutputAutoSorted: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly circuitbuilderwrapper_withOutputSorted: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly circuitbuilderwrapper_withStateMode: (a: number, b: number, c: number) => [number, number, number];
  readonly definitionregionwrapper_addBounds: (a: number, b: any, c: any) => [number, number, number];
  readonly definitionregionwrapper_addFilter: (a: number, b: number, c: number) => [number, number, number];
  readonly definitionregionwrapper_addPoint: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_boxCount: (a: number) => number;
  readonly definitionregionwrapper_center: (a: number) => any;
  readonly definitionregionwrapper_centerF32: (a: number) => any;
  readonly definitionregionwrapper_clone: (a: number) => number;
  readonly definitionregionwrapper_connectedComponents: (a: number) => number;
  readonly definitionregionwrapper_contains: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_contract: (a: number, b: number) => number;
  readonly definitionregionwrapper_contracted: (a: number, b: number) => number;
  readonly definitionregionwrapper_dimensions: (a: number) => any;
  readonly definitionregionwrapper_excludeBlock: (a: number, b: number, c: number) => [number, number, number];
  readonly definitionregionwrapper_expand: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_expanded: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_filterByBlock: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_filterByProperties: (a: number, b: number, c: any) => [number, number, number];
  readonly definitionregionwrapper_fromBoundingBoxes: (a: any) => [number, number, number];
  readonly definitionregionwrapper_fromBounds: (a: number, b: number) => number;
  readonly definitionregionwrapper_fromPositions: (a: any) => [number, number, number];
  readonly definitionregionwrapper_getAllMetadata: (a: number) => any;
  readonly definitionregionwrapper_getBlocks: (a: number) => [number, number, number];
  readonly definitionregionwrapper_getBounds: (a: number) => any;
  readonly definitionregionwrapper_getBox: (a: number, b: number) => any;
  readonly definitionregionwrapper_getBoxes: (a: number) => any;
  readonly definitionregionwrapper_getMetadata: (a: number, b: number, c: number) => any;
  readonly definitionregionwrapper_intersect: (a: number, b: number) => number;
  readonly definitionregionwrapper_intersected: (a: number, b: number) => number;
  readonly definitionregionwrapper_intersectsBounds: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => number;
  readonly definitionregionwrapper_isContiguous: (a: number) => number;
  readonly definitionregionwrapper_isEmpty: (a: number) => number;
  readonly definitionregionwrapper_merge: (a: number, b: number) => number;
  readonly definitionregionwrapper_metadataKeys: (a: number) => any;
  readonly definitionregionwrapper_new: () => number;
  readonly definitionregionwrapper_positions: (a: number) => any;
  readonly definitionregionwrapper_positionsSorted: (a: number) => any;
  readonly definitionregionwrapper_setColor: (a: number, b: number) => number;
  readonly definitionregionwrapper_setMetadata: (a: number, b: number, c: number, d: number, e: number) => number;
  readonly definitionregionwrapper_shift: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_shifted: (a: number, b: number, c: number, d: number) => number;
  readonly definitionregionwrapper_simplify: (a: number) => number;
  readonly definitionregionwrapper_subtract: (a: number, b: number) => number;
  readonly definitionregionwrapper_subtracted: (a: number, b: number) => number;
  readonly definitionregionwrapper_union: (a: number, b: number) => number;
  readonly definitionregionwrapper_unionInto: (a: number, b: number) => number;
  readonly definitionregionwrapper_volume: (a: number) => number;
  readonly executionmodewrapper_fixedTicks: (a: number) => number;
  readonly executionmodewrapper_untilChange: (a: number, b: number) => number;
  readonly executionmodewrapper_untilCondition: (a: number, b: number, c: number, d: number, e: number) => number;
  readonly executionmodewrapper_untilStable: (a: number, b: number) => number;
  readonly iolayoutbuilderwrapper_addInput: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addInputAuto: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addInputFromRegion: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addInputFromRegionAuto: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addInputRegion: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addInputRegionAuto: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutput: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutputAuto: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutputFromRegion: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutputFromRegionAuto: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutputRegion: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_addOutputRegionAuto: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number, number];
  readonly iolayoutbuilderwrapper_build: (a: number) => number;
  readonly iolayoutbuilderwrapper_new: () => number;
  readonly iolayoutwrapper_inputNames: (a: number) => [number, number];
  readonly iolayoutwrapper_outputNames: (a: number) => [number, number];
  readonly iotypewrapper_ascii: (a: number) => number;
  readonly iotypewrapper_boolean: () => number;
  readonly iotypewrapper_float32: () => number;
  readonly iotypewrapper_signedInt: (a: number) => number;
  readonly iotypewrapper_unsignedInt: (a: number) => number;
  readonly layoutfunctionwrapper_columnMajor: (a: number, b: number, c: number) => number;
  readonly layoutfunctionwrapper_custom: (a: number, b: number) => number;
  readonly layoutfunctionwrapper_oneToOne: () => number;
  readonly layoutfunctionwrapper_packed4: () => number;
  readonly layoutfunctionwrapper_rowMajor: (a: number, b: number, c: number) => number;
  readonly layoutfunctionwrapper_scanline: (a: number, b: number, c: number) => number;
  readonly mchprsworldwrapper_checkCustomIoChanges: (a: number) => void;
  readonly mchprsworldwrapper_clearCustomIoChanges: (a: number) => void;
  readonly mchprsworldwrapper_flush: (a: number) => void;
  readonly mchprsworldwrapper_getSignalStrength: (a: number, b: number, c: number, d: number) => number;
  readonly mchprsworldwrapper_get_lever_power: (a: number, b: number, c: number, d: number) => number;
  readonly mchprsworldwrapper_get_redstone_power: (a: number, b: number, c: number, d: number) => number;
  readonly mchprsworldwrapper_get_schematic: (a: number) => number;
  readonly mchprsworldwrapper_get_truth_table: (a: number) => any;
  readonly mchprsworldwrapper_into_schematic: (a: number) => number;
  readonly mchprsworldwrapper_is_lit: (a: number, b: number, c: number, d: number) => number;
  readonly mchprsworldwrapper_new: (a: number) => [number, number, number];
  readonly mchprsworldwrapper_on_use_block: (a: number, b: number, c: number, d: number) => void;
  readonly mchprsworldwrapper_peekCustomIoChanges: (a: number) => any;
  readonly mchprsworldwrapper_pollCustomIoChanges: (a: number) => any;
  readonly mchprsworldwrapper_setSignalStrength: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly mchprsworldwrapper_sync_to_schematic: (a: number) => void;
  readonly mchprsworldwrapper_tick: (a: number, b: number) => void;
  readonly mchprsworldwrapper_with_options: (a: number, b: number) => [number, number, number];
  readonly outputconditionwrapper_bitwiseAnd: (a: number) => number;
  readonly outputconditionwrapper_equals: (a: number) => number;
  readonly outputconditionwrapper_greaterThan: (a: number) => number;
  readonly outputconditionwrapper_lessThan: (a: number) => number;
  readonly outputconditionwrapper_notEquals: (a: number) => number;
  readonly schematicbuilderwrapper_build: (a: number) => [number, number, number];
  readonly schematicbuilderwrapper_fromTemplate: (a: number, b: number) => [number, number, number];
  readonly schematicbuilderwrapper_map: (a: number, b: number, c: number, d: number) => number;
  readonly schematicbuilderwrapper_name: (a: number, b: number, c: number) => number;
  readonly schematicbuilderwrapper_new: () => number;
  readonly simulationoptionswrapper_addCustomIo: (a: number, b: number, c: number, d: number) => void;
  readonly simulationoptionswrapper_clearCustomIo: (a: number) => void;
  readonly simulationoptionswrapper_io_only: (a: number) => number;
  readonly simulationoptionswrapper_new: () => number;
  readonly simulationoptionswrapper_optimize: (a: number) => number;
  readonly simulationoptionswrapper_set_io_only: (a: number, b: number) => void;
  readonly simulationoptionswrapper_set_optimize: (a: number, b: number) => void;
  readonly sortstrategywrapper_descending: () => number;
  readonly sortstrategywrapper_distanceFrom: (a: number, b: number, c: number) => number;
  readonly sortstrategywrapper_distanceFromDesc: (a: number, b: number, c: number) => number;
  readonly sortstrategywrapper_fromString: (a: number, b: number) => [number, number, number];
  readonly sortstrategywrapper_name: (a: number) => [number, number];
  readonly sortstrategywrapper_preserve: () => number;
  readonly sortstrategywrapper_reverse: () => number;
  readonly sortstrategywrapper_xDescYZ: () => number;
  readonly sortstrategywrapper_xyz: () => number;
  readonly sortstrategywrapper_yxz: () => number;
  readonly sortstrategywrapper_zDescYX: () => number;
  readonly statemodeconstants_manual: () => [number, number];
  readonly statemodeconstants_stateful: () => [number, number];
  readonly statemodeconstants_stateless: () => [number, number];
  readonly typedcircuitexecutorwrapper_execute: (a: number, b: any, c: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_flush: (a: number) => void;
  readonly typedcircuitexecutorwrapper_fromInsign: (a: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_fromInsignWithOptions: (a: number, b: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_fromLayout: (a: number, b: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_fromLayoutWithOptions: (a: number, b: number, c: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_getLayoutInfo: (a: number) => any;
  readonly typedcircuitexecutorwrapper_inputNames: (a: number) => [number, number];
  readonly typedcircuitexecutorwrapper_outputNames: (a: number) => [number, number];
  readonly typedcircuitexecutorwrapper_readOutput: (a: number, b: number, c: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_reset: (a: number) => [number, number];
  readonly typedcircuitexecutorwrapper_run: (a: number, b: any, c: number, d: number, e: number) => [number, number, number];
  readonly typedcircuitexecutorwrapper_setInput: (a: number, b: number, c: number, d: number) => [number, number];
  readonly typedcircuitexecutorwrapper_setStateMode: (a: number, b: number, c: number) => [number, number];
  readonly typedcircuitexecutorwrapper_syncToSchematic: (a: number) => number;
  readonly typedcircuitexecutorwrapper_tick: (a: number, b: number) => void;
  readonly valuewrapper_fromBool: (a: number) => number;
  readonly valuewrapper_fromF32: (a: number) => number;
  readonly valuewrapper_fromI32: (a: number) => number;
  readonly valuewrapper_fromString: (a: number, b: number) => number;
  readonly valuewrapper_fromU32: (a: number) => number;
  readonly valuewrapper_toJs: (a: number) => any;
  readonly valuewrapper_typeName: (a: number) => [number, number];
  readonly schematicwrapper_create_simulation_world_with_options: (a: number, b: number) => [number, number, number];
  readonly sortstrategywrapper_yDescXZ: () => number;
  readonly sortstrategywrapper_zyx: () => number;
  readonly definitionregionwrapper_copy: (a: number) => number;
  readonly schematicwrapper_create_simulation_world: (a: number) => [number, number, number];
  readonly __wbg_blockposition_free: (a: number, b: number) => void;
  readonly __wbg_get_blockposition_x: (a: number) => number;
  readonly __wbg_get_blockposition_y: (a: number) => number;
  readonly __wbg_get_blockposition_z: (a: number) => number;
  readonly __wbg_set_blockposition_x: (a: number, b: number) => void;
  readonly __wbg_set_blockposition_y: (a: number, b: number) => void;
  readonly __wbg_set_blockposition_z: (a: number, b: number) => void;
  readonly blockposition_new: (a: number, b: number, c: number) => number;
  readonly __wbg_blockstatewrapper_free: (a: number, b: number) => void;
  readonly __wbg_lazychunkiterator_free: (a: number, b: number) => void;
  readonly __wbg_schematicwrapper_free: (a: number, b: number) => void;
  readonly blockstatewrapper_name: (a: number) => [number, number];
  readonly blockstatewrapper_new: (a: number, b: number) => number;
  readonly blockstatewrapper_properties: (a: number) => any;
  readonly blockstatewrapper_with_property: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly debug_json_schematic: (a: number) => [number, number];
  readonly debug_schematic: (a: number) => [number, number];
  readonly lazychunkiterator_current_position: (a: number) => number;
  readonly lazychunkiterator_has_next: (a: number) => number;
  readonly lazychunkiterator_next: (a: number) => any;
  readonly lazychunkiterator_reset: (a: number) => void;
  readonly lazychunkiterator_skip_to: (a: number, b: number) => void;
  readonly lazychunkiterator_total_chunks: (a: number) => number;
  readonly schematicwrapper_addDefinitionRegion: (a: number, b: number, c: number, d: number) => void;
  readonly schematicwrapper_blocks: (a: number) => any;
  readonly schematicwrapper_blocks_indices: (a: number) => any;
  readonly schematicwrapper_buildExecutor: (a: number, b: any) => [number, number, number];
  readonly schematicwrapper_chunks: (a: number, b: number, c: number, d: number) => any;
  readonly schematicwrapper_chunks_indices: (a: number, b: number, c: number, d: number) => any;
  readonly schematicwrapper_chunks_indices_with_strategy: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => any;
  readonly schematicwrapper_chunks_with_strategy: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => any;
  readonly schematicwrapper_compileInsign: (a: number) => [number, number, number];
  readonly schematicwrapper_copy_region: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number, j: number, k: number, l: any) => [number, number];
  readonly schematicwrapper_createCircuit: (a: number, b: any, c: any) => [number, number, number];
  readonly schematicwrapper_createCircuitBuilder: (a: number) => number;
  readonly schematicwrapper_createDefinitionRegion: (a: number, b: number, c: number) => void;
  readonly schematicwrapper_createDefinitionRegionFromBounds: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly schematicwrapper_createDefinitionRegionFromPoint: (a: number, b: number, c: number, d: number, e: number, f: number) => void;
  readonly schematicwrapper_createRegion: (a: number, b: number, c: number, d: any, e: any) => [number, number, number];
  readonly schematicwrapper_create_lazy_chunk_iterator: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => number;
  readonly schematicwrapper_debug_info: (a: number) => [number, number];
  readonly schematicwrapper_definitionRegionAddBounds: (a: number, b: number, c: number, d: number, e: number) => [number, number];
  readonly schematicwrapper_definitionRegionAddPoint: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number];
  readonly schematicwrapper_definitionRegionSetMetadata: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => [number, number];
  readonly schematicwrapper_definitionRegionShift: (a: number, b: number, c: number, d: number, e: number, f: number) => [number, number];
  readonly schematicwrapper_extractSigns: (a: number) => any;
  readonly schematicwrapper_fillCuboid: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => void;
  readonly schematicwrapper_fillSphere: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => void;
  readonly schematicwrapper_flip_region_x: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_flip_region_y: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_flip_region_z: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_flip_x: (a: number) => void;
  readonly schematicwrapper_flip_y: (a: number) => void;
  readonly schematicwrapper_flip_z: (a: number) => void;
  readonly schematicwrapper_from_data: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_from_litematic: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_from_schematic: (a: number, b: number, c: number) => [number, number];
  readonly schematicwrapper_getChunkData: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
  readonly schematicwrapper_getDefinitionRegion: (a: number, b: number, c: number) => [number, number, number];
  readonly schematicwrapper_getDefinitionRegionNames: (a: number) => any;
  readonly schematicwrapper_get_all_block_entities: (a: number) => any;
  readonly schematicwrapper_get_all_palettes: (a: number) => any;
  readonly schematicwrapper_get_allocated_dimensions: (a: number) => [number, number];
  readonly schematicwrapper_get_available_schematic_versions: (a: number) => any;
  readonly schematicwrapper_get_block: (a: number, b: number, c: number, d: number) => [number, number];
  readonly schematicwrapper_get_block_count: (a: number) => number;
  readonly schematicwrapper_get_block_entity: (a: number, b: number, c: number, d: number) => any;
  readonly schematicwrapper_get_block_string: (a: number, b: number, c: number, d: number) => [number, number];
  readonly schematicwrapper_get_block_with_properties: (a: number, b: number, c: number, d: number) => number;
  readonly schematicwrapper_get_bounding_box: (a: number) => any;
  readonly schematicwrapper_get_chunk_blocks: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
  readonly schematicwrapper_get_chunk_blocks_indices: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
  readonly schematicwrapper_get_default_format_version: (a: number, b: number) => [number, number];
  readonly schematicwrapper_get_default_region_palette: (a: number) => any;
  readonly schematicwrapper_get_dimensions: (a: number) => [number, number];
  readonly schematicwrapper_get_format_versions: (a: number, b: number) => any;
  readonly schematicwrapper_get_optimization_info: (a: number) => any;
  readonly schematicwrapper_get_palette: (a: number) => any;
  readonly schematicwrapper_get_palette_from_region: (a: number, b: number, c: number) => any;
  readonly schematicwrapper_get_region_bounding_box: (a: number, b: number, c: number) => any;
  readonly schematicwrapper_get_region_names: (a: number) => [number, number];
  readonly schematicwrapper_get_supported_export_formats: () => any;
  readonly schematicwrapper_get_supported_import_formats: () => any;
  readonly schematicwrapper_get_tight_bounds_max: (a: number) => [number, number];
  readonly schematicwrapper_get_tight_bounds_min: (a: number) => [number, number];
  readonly schematicwrapper_get_tight_dimensions: (a: number) => [number, number];
  readonly schematicwrapper_get_volume: (a: number) => number;
  readonly schematicwrapper_new: () => number;
  readonly schematicwrapper_print_schematic: (a: number) => [number, number];
  readonly schematicwrapper_removeDefinitionRegion: (a: number, b: number, c: number) => number;
  readonly schematicwrapper_rotate_region_x: (a: number, b: number, c: number, d: number) => [number, number];
  readonly schematicwrapper_rotate_region_y: (a: number, b: number, c: number, d: number) => [number, number];
  readonly schematicwrapper_rotate_region_z: (a: number, b: number, c: number, d: number) => [number, number];
  readonly schematicwrapper_rotate_x: (a: number, b: number) => void;
  readonly schematicwrapper_rotate_y: (a: number, b: number) => void;
  readonly schematicwrapper_rotate_z: (a: number, b: number) => void;
  readonly schematicwrapper_save_as: (a: number, b: number, c: number, d: number, e: number) => [number, number, number, number];
  readonly schematicwrapper_setBlockWithNbt: (a: number, b: number, c: number, d: number, e: number, f: number, g: any) => [number, number];
  readonly schematicwrapper_set_block: (a: number, b: number, c: number, d: number, e: number, f: number) => void;
  readonly schematicwrapper_set_block_with_properties: (a: number, b: number, c: number, d: number, e: number, f: number, g: any) => [number, number];
  readonly schematicwrapper_to_litematic: (a: number) => [number, number, number, number];
  readonly schematicwrapper_to_schematic: (a: number) => [number, number, number, number];
  readonly schematicwrapper_to_schematic_version: (a: number, b: number, c: number) => [number, number, number, number];
  readonly start: () => void;
  readonly schematicwrapper_updateRegion: (a: number, b: number, c: number, d: number) => void;
  readonly __wbg_brushwrapper_free: (a: number, b: number) => void;
  readonly __wbg_palettemanager_free: (a: number, b: number) => void;
  readonly __wbg_shapewrapper_free: (a: number, b: number) => void;
  readonly __wbg_wasmbuildingtool_free: (a: number, b: number) => void;
  readonly brushwrapper_color: (a: number, b: number, c: number, d: number, e: number) => number;
  readonly brushwrapper_linear_gradient: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number, j: number, k: number, l: number, m: number, n: number, o: number) => number;
  readonly brushwrapper_point_gradient: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => [number, number, number];
  readonly brushwrapper_shaded: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number) => number;
  readonly brushwrapper_solid: (a: number, b: number) => [number, number, number];
  readonly palettemanager_getConcreteBlocks: () => [number, number];
  readonly palettemanager_getPaletteByKeywords: (a: number, b: number) => [number, number];
  readonly palettemanager_getTerracottaBlocks: () => [number, number];
  readonly palettemanager_getWoolBlocks: () => [number, number];
  readonly shapewrapper_cuboid: (a: number, b: number, c: number, d: number, e: number, f: number) => number;
  readonly shapewrapper_sphere: (a: number, b: number, c: number, d: number) => number;
  readonly wasmbuildingtool_fill: (a: number, b: number, c: number) => void;
  readonly generate_gradient_between_blocks: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => any;
  readonly generate_gradient_between_colors: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number, j: number, k: number) => any;
  readonly get_all_colored_blocks: () => any;
  readonly get_block_info: (a: number, b: number) => any;
  readonly get_color_spaces: () => any;
  readonly get_easing_functions: () => any;
  readonly sort_blocks_by_color_gradient: (a: number, b: number) => any;
  readonly __wbindgen_malloc: (a: number, b: number) => number;
  readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
  readonly __wbindgen_free: (a: number, b: number, c: number) => void;
  readonly __wbindgen_exn_store: (a: number) => void;
  readonly __externref_table_alloc: () => number;
  readonly __wbindgen_externrefs: WebAssembly.Table;
  readonly __externref_table_dealloc: (a: number) => void;
  readonly __externref_drop_slice: (a: number, b: number) => void;
  readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
* Instantiates the given `module`, which can either be bytes or
* a precompiled `WebAssembly.Module`.
*
* @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
*
* @returns {InitOutput}
*/
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
* If `module_or_path` is {RequestInfo} or {URL}, makes a request and
* for everything else, calls `WebAssembly.instantiate` directly.
*
* @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
*
* @returns {Promise<InitOutput>}
*/
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
